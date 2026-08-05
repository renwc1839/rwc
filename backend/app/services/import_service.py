import asyncio
import csv
import io
import json
import logging
import threading
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import import DataImport, ImportSourceType, ImportStatus
from app.models.property import Property, PropertyStatus, PropertyType
from app.services.geocoding_service import AmapGeocodingService

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"title", "address", "district", "price_monthly"}
OPTIONAL_FIELDS = {
    "description",
    "area_sqm",
    "bedrooms",
    "bathrooms",
    "property_type",
    "latitude",
    "longitude",
    "status",
}
ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
VALID_PROPERTY_TYPES = {e.value for e in PropertyType}
VALID_STATUSES = {e.value for e in PropertyStatus}


class ImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._created_property_ids: list[int] = []
        self._api_checks: list[dict[str, Any]] = []

    async def create_import_task(
        self,
        admin_id: int,
        source_name: str,
        source_type: str,
    ) -> DataImport:
        import_task = DataImport(
            admin_id=admin_id,
            source_name=source_name,
            source_type=ImportSourceType(source_type),
            status=ImportStatus.pending,
        )
        self.session.add(import_task)
        await self.session.commit()
        await self.session.refresh(import_task)
        return import_task

    async def get_import_task(self, task_id: int) -> DataImport | None:
        return await self.session.get(DataImport, task_id)

    async def list_tasks(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> list[DataImport]:
        stmt = (
            select(DataImport)
            .order_by(DataImport.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(DataImport.status == ImportStatus(status))
        result = await self.session.scalars(stmt)
        return list(result)

    async def parse_and_import(
        self,
        import_task: DataImport,
        file_content: bytes,
        landlord_id: int,
    ) -> DataImport:
        self._created_property_ids = []
        self._api_checks = []
        import_task.status = ImportStatus.processing
        await self.session.commit()

        errors: list[dict] = []
        try:
            rows = self._parse_file(file_content, import_task.source_type)
            if not rows:
                import_task.status = ImportStatus.failed
                import_task.error_log = json.dumps(
                    [{"row": 0, "error": "No data rows found in file"}],
                    ensure_ascii=False,
                )
                await self.session.commit()
                return import_task

            import_task.total_records = len(rows)
            success = 0
            failed = 0
            abnormal_items: list[dict[str, Any]] = []

            for idx, row in enumerate(rows):
                abnormal_items.extend(self._inspect_raw_row(row, idx + 1))
                try:
                    validated = self._validate_row(row, idx + 1)
                    await self._insert_property(validated, landlord_id, idx + 1)
                    success += 1
                except ValueError as exc:
                    failed += 1
                    errors.append({"row": idx + 1, "error": str(exc), "data": row})

            import_task.success_records = success
            import_task.failed_records = failed
            import_task.status = ImportStatus.completed if failed == 0 else ImportStatus.completed

            inspection = self._build_inspection(
                import_task=import_task,
                row_count=len(rows),
                abnormal_items=abnormal_items,
            )
            import_task.error_log = self._encode_import_log(errors, inspection)

            import_task.updated_at = datetime.now(timezone.utc)
            await self.session.commit()

            if success > 0:
                self._dispatch_batch_embedding()
                self._dispatch_batch_poi_generation(self._created_property_ids)

            return import_task

        except Exception as exc:
            import_task.status = ImportStatus.failed
            inspection = self._build_inspection(
                import_task=import_task,
                row_count=import_task.total_records,
                abnormal_items=[
                    {
                        "level": "critical",
                        "row": 0,
                        "type": "import_crashed",
                        "message": str(exc),
                    }
                ],
            )
            import_task.error_log = self._encode_import_log(
                [{"row": 0, "error": str(exc)}],
                inspection,
            )
            await self.session.commit()
            logger.exception("Import task %s failed", import_task.id)
            return import_task

    async def retry_failed(self, import_task: DataImport, landlord_id: int) -> DataImport:
        self._created_property_ids = []
        self._api_checks = []
        if not import_task.error_log:
            return import_task

        try:
            raw_payload = json.loads(import_task.error_log)
        except json.JSONDecodeError:
            return import_task

        error_entries = self.extract_errors(raw_payload)
        if not error_entries:
            return import_task

        import_task.status = ImportStatus.processing
        import_task.failed_records = 0
        import_task.error_log = None
        await self.session.commit()

        new_errors: list[dict] = []
        success_count = 0

        for entry in error_entries:
            row_data = entry.get("data")
            if not row_data:
                new_errors.append(entry)
                continue
            try:
                validated = self._validate_row(row_data, entry.get("row", 0))
                await self._insert_property(validated, landlord_id, entry.get("row", 0))
                success_count += 1
            except ValueError as exc:
                new_errors.append({"row": entry.get("row", 0), "error": str(exc), "data": row_data})

        import_task.success_records += success_count
        import_task.failed_records = len(new_errors)
        inspection = self._build_inspection(
            import_task=import_task,
            row_count=import_task.total_records,
            abnormal_items=[],
        )
        import_task.error_log = self._encode_import_log(new_errors, inspection)
        import_task.status = ImportStatus.completed
        import_task.updated_at = datetime.now(timezone.utc)
        await self.session.commit()

        if success_count > 0:
            self._dispatch_batch_embedding()
            self._dispatch_batch_poi_generation(self._created_property_ids)

        return import_task

    # ---- private helpers ----

    def _parse_file(self, content: bytes, source_type: ImportSourceType) -> list[dict]:
        if source_type == ImportSourceType.csv:
            return self._parse_csv(content)
        elif source_type == ImportSourceType.excel:
            return self._parse_excel(content)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    def _parse_csv(self, content: bytes) -> list[dict]:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            cleaned = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
            rows.append(cleaned)
        return rows

    def _parse_excel(self, content: bytes) -> list[dict]:
        try:
            import openpyxl
        except ImportError:
            raise ValueError("openpyxl is required for Excel import. Install it: pip install openpyxl")

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        if not ws:
            raise ValueError("No active sheet found in Excel file")

        rows_iter = ws.iter_rows(values_only=True)
        headers_raw = next(rows_iter, None)
        if not headers_raw:
            return []

        headers = [str(h).strip().lower() if h else "" for h in headers_raw]
        rows = []
        for row in rows_iter:
            if not any(row):
                continue
            cleaned = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    cleaned[headers[i]] = str(value).strip() if value is not None else ""
            rows.append(cleaned)
        wb.close()
        return rows

    def _validate_row(self, row: dict, row_num: int) -> dict:
        missing = REQUIRED_FIELDS - set(row.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        validated: dict = {}

        title = str(row.get("title", "")).strip()
        if not title:
            raise ValueError("title is empty")
        validated["title"] = title

        address = str(row.get("address", "")).strip()
        if not address:
            raise ValueError("address is empty")
        validated["address"] = address

        district = str(row.get("district", "")).strip()
        if not district:
            raise ValueError("district is empty")
        validated["district"] = district

        try:
            price = Decimal(str(row.get("price_monthly", "0")).strip())
            if price < 0:
                raise ValueError(f"price_monthly must be non-negative, got {price}")
            validated["price_monthly"] = price
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Invalid price_monthly: {exc}") from exc

        # Optional fields
        if row.get("description"):
            validated["description"] = str(row["description"]).strip()

        if row.get("area_sqm"):
            try:
                area = Decimal(str(row["area_sqm"]).strip())
                if area <= 0:
                    raise ValueError(f"area_sqm must be positive, got {area}")
                validated["area_sqm"] = area
            except (InvalidOperation, ValueError):
                pass

        if row.get("bedrooms", "").strip():
            try:
                bedrooms = int(row["bedrooms"])
                if bedrooms < 0:
                    raise ValueError(f"bedrooms must be non-negative, got {bedrooms}")
                validated["bedrooms"] = bedrooms
            except ValueError:
                pass

        if row.get("bathrooms", "").strip():
            try:
                bathrooms = int(row["bathrooms"])
                if bathrooms < 0:
                    raise ValueError(f"bathrooms must be non-negative, got {bathrooms}")
                validated["bathrooms"] = bathrooms
            except ValueError:
                pass

        if row.get("property_type", "").strip():
            ptype = str(row["property_type"]).strip().lower()
            if ptype not in VALID_PROPERTY_TYPES:
                raise ValueError(
                    f"Invalid property_type '{ptype}'. Must be one of: {VALID_PROPERTY_TYPES}"
                )
            validated["property_type"] = ptype

        if row.get("status", "").strip():
            pstatus = str(row["status"]).strip().lower()
            if pstatus not in VALID_STATUSES:
                raise ValueError(
                    f"Invalid status '{pstatus}'. Must be one of: {VALID_STATUSES}"
                )
            validated["status"] = pstatus

        if row.get("latitude", "").strip() and row.get("longitude", "").strip():
            try:
                lat = Decimal(str(row["latitude"]).strip())
                lng = Decimal(str(row["longitude"]).strip())
                if not (-90 <= float(lat) <= 90):
                    raise ValueError(f"latitude out of range: {lat}")
                if not (-180 <= float(lng) <= 180):
                    raise ValueError(f"longitude out of range: {lng}")
                validated["latitude"] = lat
                validated["longitude"] = lng
            except (InvalidOperation, ValueError):
                pass

        return validated

    async def _insert_property(self, data: dict, landlord_id: int, row_num: int) -> None:
        # Deduplication: check by title + address
        existing = await self.session.scalar(
            select(Property).where(
                and_(
                    Property.title == data["title"],
                    Property.address == data["address"],
                )
            )
        )
        if existing:
            raise ValueError(f"Duplicate: property with title '{data['title']}' and address '{data['address']}' already exists")

        property_obj = Property(
            landlord_id=landlord_id,
            title=data["title"],
            address=data["address"],
            district=data["district"],
            price_monthly=data["price_monthly"],
            description=data.get("description"),
            area_sqm=data.get("area_sqm"),
            bedrooms=data.get("bedrooms", 0),
            bathrooms=data.get("bathrooms", 0),
            property_type=PropertyType(data.get("property_type", "apartment")),
            status=PropertyStatus(data.get("status", "available")),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )
        self.session.add(property_obj)
        await self.session.flush()
        await self._fill_location_from_api(property_obj, row_num)
        self._created_property_ids.append(property_obj.id)

    async def _fill_location_from_api(self, property_obj: Property, row_num: int) -> None:
        if property_obj.latitude is not None and property_obj.longitude is not None:
            self._api_checks.append(
                {
                    "row": row_num,
                    "property_id": property_obj.id,
                    "service": "amap_geocode",
                    "status": "skipped",
                    "message": "文件已提供经纬度，未重复调用地理编码 API",
                }
            )
            return

        try:
            result = await AmapGeocodingService().geocode(
                property_obj.address,
                property_obj.district,
            )
            property_obj.latitude = result.latitude
            property_obj.longitude = result.longitude
            self._api_checks.append(
                {
                    "row": row_num,
                    "property_id": property_obj.id,
                    "service": "amap_geocode",
                    "status": "success",
                    "message": result.formatted_address or "地理编码成功",
                }
            )
        except RuntimeError as exc:
            self._api_checks.append(
                {
                    "row": row_num,
                    "property_id": property_obj.id,
                    "service": "amap_geocode",
                    "status": "warning",
                    "message": str(exc),
                }
            )
        except Exception as exc:
            self._api_checks.append(
                {
                    "row": row_num,
                    "property_id": property_obj.id,
                    "service": "amap_geocode",
                    "status": "failed",
                    "message": str(exc),
                }
            )

    def _inspect_raw_row(self, row: dict, row_num: int) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        unknown_fields = sorted(set(row.keys()) - ALL_FIELDS)
        if unknown_fields:
            items.append(
                {
                    "level": "notice",
                    "row": row_num,
                    "type": "unknown_fields",
                    "message": f"存在未识别字段：{', '.join(unknown_fields)}",
                }
            )

        price_text = str(row.get("price_monthly", "")).strip()
        if price_text:
            try:
                price = Decimal(price_text)
                if price == 0:
                    items.append(
                        {
                            "level": "warning",
                            "row": row_num,
                            "type": "zero_price",
                            "message": "月租为 0，需要确认是否为录入错误",
                        }
                    )
                elif price > Decimal("200000"):
                    items.append(
                        {
                            "level": "warning",
                            "row": row_num,
                            "type": "price_outlier",
                            "message": f"月租 {price} 明显偏高，需要复核",
                        }
                    )
            except InvalidOperation:
                pass

        area_text = str(row.get("area_sqm", "")).strip()
        if area_text:
            try:
                area = Decimal(area_text)
                if area < Decimal("5") or area > Decimal("1000"):
                    items.append(
                        {
                            "level": "warning",
                            "row": row_num,
                            "type": "area_outlier",
                            "message": f"面积 {area} 平方米不在常见范围内",
                        }
                    )
            except InvalidOperation:
                items.append(
                    {
                        "level": "notice",
                        "row": row_num,
                        "type": "invalid_optional_area",
                        "message": "面积字段无法解析，已按空值导入",
                    }
                )

        for field_name in ("bedrooms", "bathrooms"):
            value_text = str(row.get(field_name, "")).strip()
            if not value_text:
                continue
            try:
                value = int(value_text)
                if value > 10:
                    items.append(
                        {
                            "level": "warning",
                            "row": row_num,
                            "type": f"{field_name}_outlier",
                            "message": f"{field_name}={value} 明显偏高，需要复核",
                        }
                    )
            except ValueError:
                items.append(
                    {
                        "level": "notice",
                        "row": row_num,
                        "type": f"invalid_optional_{field_name}",
                        "message": f"{field_name} 无法解析，已按默认值导入",
                    }
                )

        return items

    def _build_inspection(
        self,
        *,
        import_task: DataImport,
        row_count: int,
        abnormal_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        api_failed = [
            item for item in self._api_checks
            if item.get("status") in {"failed", "warning"}
        ]
        if api_failed:
            abnormal_items.extend(
                {
                    "level": "warning" if item.get("status") == "warning" else "critical",
                    "row": item.get("row", 0),
                    "type": "api_check_failed",
                    "message": f"{item.get('service')}：{item.get('message')}",
                    "property_id": item.get("property_id"),
                }
                for item in api_failed
            )

        failure_rate = (import_task.failed_records / row_count) if row_count else 0
        if import_task.failed_records > 0:
            abnormal_items.append(
                {
                    "level": "critical" if failure_rate >= 0.3 else "warning",
                    "row": 0,
                    "type": "failed_records",
                    "message": f"{import_task.failed_records} 条房源导入失败，失败率 {failure_rate:.0%}",
                }
            )

        levels = {item.get("level") for item in abnormal_items}
        if "critical" in levels:
            level = "critical"
        elif "warning" in levels:
            level = "warning"
        elif "notice" in levels:
            level = "notice"
        else:
            level = "normal"

        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "summary": {
                "total": row_count,
                "success": import_task.success_records,
                "failed": import_task.failed_records,
                "abnormal": len(abnormal_items),
                "api_success": len([item for item in self._api_checks if item.get("status") == "success"]),
                "api_failed": len(api_failed),
                "api_skipped": len([item for item in self._api_checks if item.get("status") == "skipped"]),
            },
            "api_checks": self._api_checks,
            "abnormal_items": abnormal_items,
        }

    @staticmethod
    def _encode_import_log(errors: list[dict[str, Any]], inspection: dict[str, Any]) -> str | None:
        if not errors and inspection.get("level") == "normal":
            return None
        return json.dumps(
            {
                "errors": errors,
                "inspection": inspection,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def extract_errors(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            errors = payload.get("errors")
            return errors if isinstance(errors, list) else []
        return []

    @staticmethod
    def extract_inspection(payload: Any) -> dict[str, Any] | None:
        if isinstance(payload, dict) and isinstance(payload.get("inspection"), dict):
            return payload["inspection"]
        return None

    @staticmethod
    def _dispatch_batch_embedding() -> None:
        def _run() -> None:
            try:
                from app.tasks.import_tasks import batch_embedding_new_properties
                batch_embedding_new_properties.delay()
            except Exception:
                logger.exception("Failed to dispatch batch embedding task")

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _dispatch_batch_poi_generation(self, property_ids: list[int]) -> None:
        if not property_ids:
            return

        def _run() -> None:
            try:
                from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

                from app.core.config import get_settings
                from app.models.property import Property
                from app.services.poi_service import POIService

                async def _generate() -> None:
                    engine = create_async_engine(get_settings().database_url)
                    try:
                        maker = async_sessionmaker(engine, expire_on_commit=False)
                        async with maker() as session:
                            poi_service = POIService(session)
                            for property_id in property_ids:
                                try:
                                    prop = await session.get(Property, property_id)
                                    if prop:
                                        await poi_service.generate_poi_for_property(prop, force=True)
                                except Exception:
                                    logger.exception("Failed to generate POI for imported property %s", property_id)
                    finally:
                        await engine.dispose()

                asyncio.run(_generate())
            except Exception:
                logger.exception("Failed to dispatch batch POI generation")

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

#!/usr/bin/env python3
"""
Seed llmmodel table from models-original.csv.

Uses provider_name -> primary_provider_type_id mapping from debugging-llm-catalogs.md.

Usage:
    cd backend && uv run python app/test_scripts/llm_catalog_loader/seed_models.py
    # or with docker:
    docker compose exec backend uv run python app/test_scripts/llm_catalog_loader/seed_models.py
"""
import csv
import sys
import uuid
from pathlib import Path

# Add backend to path (seed_models.py -> llm_catalog_loader -> test_scripts -> app -> backend)
backend_path = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlmodel import Session, select

from app.core.db import engine
from app.models import LLMModel, LLMProviderType, User

# provider_name -> primary_provider_type_id (from debugging-llm-catalogs.md)
PROVIDER_TYPE_IDS = {
    "OpenAI": "673f1787-8474-4e1c-986c-8e19f14c989c",
    "Anthropic": "008dc763-4309-43cd-ba5f-1eb1323a0964",
    "OpenAI Compatible": "e09ade10-8563-4748-8deb-1a6c87c97134",
    "Custom": "186672e2-f50a-4457-a7dd-a50084077ff7",
    "Empty": "37520103-0644-4d29-99b6-583eb0996370",  # fix if doc has typo: 637 -> 6370 (12 hex chars)
    "Google": "ae07eb0b-929e-4844-8b75-4fe6abca09df",
}


def parse_bool(val: str | None) -> bool:
    if not val or not str(val).strip():
        return False
    return str(val).strip().lower() in ("true", "1", "yes", "t")


def parse_int(val: str | None) -> int | None:
    if not val or not str(val).strip():
        return None
    return int(val.strip())


def main() -> None:
    script_dir = Path(__file__).parent
    csv_path = script_dir / "models-original.csv"

    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        sys.exit(1)

    with Session(engine) as session:
        # Get owner_id: first user or fallback
        owner = session.exec(select(User).limit(1)).first()
        if not owner:
            print("⚠️  No user found. Using placeholder owner_id.")
            owner_id = uuid.UUID("55c5b05a-72b1-42d4-ba82-a128ddabbedd")
        else:
            owner_id = owner.id
            print(f"Using owner: {owner.email} ({owner_id})")

        # Verify provider types exist (skip malformed UUIDs)
        for name, pt_id in PROVIDER_TYPE_IDS.items():
            try:
                pt_uuid = uuid.UUID(pt_id)
            except ValueError:
                print(f"⚠️  Skipping provider type '{name}' - invalid UUID: {pt_id}")
                continue
            pt = session.get(LLMProviderType, pt_uuid)
            if not pt:
                print(f"⚠️  Provider type '{name}' ({pt_id}) not found - models for this provider will be skipped.")

        created = 0
        skipped = 0

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                provider_name = row.get("provider_name", "").strip()
                model_id = row.get("model_id", "").strip()
                display_name = row.get("display_name", "").strip()

                if not provider_name or not model_id or not display_name:
                    continue

                primary_provider_type_id_str = PROVIDER_TYPE_IDS.get(provider_name)
                if not primary_provider_type_id_str:
                    print(f"  ⏭️  Skipping '{model_id}' - unknown provider '{provider_name}'")
                    skipped += 1
                    continue

                primary_provider_type_id = uuid.UUID(primary_provider_type_id_str)

                # Check if already exists
                existing = session.exec(
                    select(LLMModel).where(
                        LLMModel.primary_provider_type_id == primary_provider_type_id,
                        LLMModel.model_id == model_id,
                    )
                ).first()

                if existing:
                    print(f"  ⏭️  Skipping '{display_name}' (already exists)")
                    skipped += 1
                    continue

                model = LLMModel(
                    model_id=model_id,
                    display_name=display_name,
                    description=row.get("description", "").strip() or None,
                    context_window=parse_int(row.get("context_window")),
                    is_default=parse_bool(row.get("is_default")),
                    is_enabled=parse_bool(row.get("is_enabled", "true")),
                    is_deprecated=False,
                    sort_order=parse_int(row.get("sort_order")) or 0,
                    has_vision=parse_bool(row.get("has_vision")) if row.get("has_vision") not in ("", None) else None,
                    has_function_calling=parse_bool(row.get("has_function_calling")) if row.get("has_function_calling") not in ("", None) else None,
                    has_streaming=parse_bool(row.get("has_streaming")) if row.get("has_streaming") not in ("", None) else None,
                    has_json_mode=parse_bool(row.get("has_json_mode")) if row.get("has_json_mode") not in ("", None) else None,
                    is_system=True,
                    multiple_provider_type_support=False,
                    primary_provider_type_id=primary_provider_type_id,
                    owner_id=owner_id,
                )
                session.add(model)
                print(f"  ✅ Created: {display_name} ({model_id}) [{provider_name}]")
                created += 1

        session.commit()
        print(f"\n✅ Done. Created {created}, skipped {skipped}.")


if __name__ == "__main__":
    main()

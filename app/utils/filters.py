from qdrant_client.http import models as q_models
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def translate_filters(store_id: str, input_filters: Optional[Dict[str, Any]] = None) -> q_models.Filter:
    """
    Translates a flexible "Bring Your Own Schema" (BYOS) filter dictionary 
    into a structured Qdrant Filter object.
    
    Logic:
    1. Always enforce store_id (Tenant Isolation).
    2. Arrays: Match any (OR).
    3. Min/Max objects: Range query.
    4. Strings/Values: Exact match.
    """
    must_conditions = []

    # 1. Enforce Tenant Isolation (Mandatory)
    must_conditions.append(
        q_models.FieldCondition(
            key="store_id",
            match=q_models.MatchValue(value=store_id)
        )
    )

    if not input_filters:
        return q_models.Filter(must=must_conditions)

    # Core fields for direct mapping (sit at root of payload)
    core_fields = ["brand", "category", "product_id"]

    for key, value in input_filters.items():
        # Determine key path (core vs nested metadata)
        field_key = key if key in core_fields else f"metadata.{key}"

        if isinstance(value, list):
            must_conditions.append(
                q_models.FieldCondition(
                    key=field_key,
                    match=q_models.MatchAny(any=value)
                )
            )

        elif isinstance(value, dict):
            range_params = {}
            if "min" in value:
                range_params["gte"] = value["min"]
            if "max" in value:
                range_params["lte"] = value["max"]
            
            if range_params:
                must_conditions.append(
                    q_models.FieldCondition(
                        key=field_key,
                        range=q_models.Range(**range_params)
                    )
                )

        else:
            must_conditions.append(
                q_models.FieldCondition(
                    key=field_key,
                    match=q_models.MatchValue(value=value)
                )
            )

    return q_models.Filter(must=must_conditions)

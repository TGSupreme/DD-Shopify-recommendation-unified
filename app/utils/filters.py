from qdrant_client.http import models as q_models
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# List of fields that live at the root level of the payload
ROOT_FIELDS = ["store_id", "product_id", "title", "description", "brand", "category", "tags"]

def translate_filters(store_id: str, input_filters: Optional[Dict[str, Any]] = None) -> q_models.Filter:
    """
    Translates standardized merchant filters into a Qdrant Filter object.
    Automatically prepends 'metadata.' to fields not in ROOT_FIELDS.
    """
    must_conditions = []

    # 1. Enforce Tenant Isolation (Root Level)
    must_conditions.append(
        q_models.FieldCondition(
            key="store_id",
            match=q_models.MatchValue(value=store_id)
        )
    )

    if not input_filters:
        return q_models.Filter(must=must_conditions)

    for key, value in input_filters.items():
        # Determine the correct indexed key (Root vs Metadata)
        indexed_key = key if key in ROOT_FIELDS else f"metadata.{key}"

        # Handle Boolean match
        if isinstance(value, bool):
            must_conditions.append(
                q_models.FieldCondition(
                    key=indexed_key,
                    match=q_models.MatchValue(value=value)
                )
            )

        # Handle Array (Match any of the values)
        elif isinstance(value, list):
            must_conditions.append(
                q_models.FieldCondition(
                    key=indexed_key,
                    match=q_models.MatchAny(any=value)
                )
            )

        # Handle Range (Min/Max object)
        elif isinstance(value, dict):
            range_params = {}
            if "min" in value:
                range_params["gte"] = value["min"]
            if "max" in value:
                range_params["lte"] = value["max"]
            
            if range_params:
                must_conditions.append(
                    q_models.FieldCondition(
                        key=indexed_key,
                        range=q_models.Range(**range_params)
                    )
                )

        # Handle Singular value (Exact Match for strings)
        else:
            must_conditions.append(
                q_models.FieldCondition(
                    key=indexed_key,
                    match=q_models.MatchValue(value=value)
                )
            )

    return q_models.Filter(must=must_conditions)

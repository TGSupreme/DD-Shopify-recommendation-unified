from qdrant_client.http import models as q_models
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def translate_filters(store_id: str, input_filters: Optional[Dict[str, Any]] = None) -> q_models.Filter:
    """
    Translates standardized merchant filters into a Qdrant Filter object.
    
    Logic:
    1. Always enforce store_id (Tenant Isolation).
    2. Arrays: Match Any (OR).
    3. Min/Max objects: Range query.
    4. Strings/Values: Match Value.
    5. Boolean: Match Value.
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

    # All standardized commerce fields now live at the root of the payload
    for key, value in input_filters.items():
        # Handle Boolean match
        if isinstance(value, bool):
            must_conditions.append(
                q_models.FieldCondition(
                    key=key,
                    match=q_models.MatchValue(value=value)
                )
            )

        # Handle Array (Match any of the values)
        elif isinstance(value, list):
            must_conditions.append(
                q_models.FieldCondition(
                    key=key,
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
                        key=key,
                        range=q_models.Range(**range_params)
                    )
                )

        # Handle Singular value (Exact Match for strings)
        else:
            must_conditions.append(
                q_models.FieldCondition(
                    key=key,
                    match=q_models.MatchValue(value=value)
                )
            )

    return q_models.Filter(must=must_conditions)

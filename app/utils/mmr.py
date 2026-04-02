import numpy as np
from typing import List, Tuple, Dict, Any

def cosine_similarity_matrix(vectors_a: np.ndarray, vectors_b: np.ndarray) -> np.ndarray:
    """
    Computes the cosine similarity matrix between two sets of vectors.
    """
    # Normalize vectors
    norm_a = np.linalg.norm(vectors_a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(vectors_b, axis=1, keepdims=True)
    
    # Avoid division by zero
    norm_a[norm_a == 0] = 1e-10
    norm_b[norm_b == 0] = 1e-10
    
    a_normalized = vectors_a / norm_a
    b_normalized = vectors_b / norm_b
    
    return np.dot(a_normalized, b_normalized.T)

def calculate_mmr(
    candidate_ids: List[str], 
    candidate_vectors: List[List[float]], 
    candidate_scores: List[float], 
    limit: int, 
    diversity_penalty: float
) -> List[Tuple[str, float]]:
    """
    Applies Maximal Marginal Relevance (MMR) to re-rank candidates for diversity.
    Uses pre-computed relevance scores from Qdrant to avoid needing the original query vector.
    
    MMR Score = (1 - diversity_penalty) * relevance_score - diversity_penalty * max_sim_to_selected
    """
    if not candidate_ids or limit <= 0:
        return []
        
    if diversity_penalty <= 0.0:
        # If no penalty, just return top N by score
        combined = list(zip(candidate_ids, candidate_scores))
        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:limit]

    # Convert to numpy arrays for fast math
    vectors = np.array(candidate_vectors)
    relevance_scores = np.array(candidate_scores)
    
    # Normalize relevance scores to [0, 1] range to be comparable with cosine similarity
    max_score = np.max(relevance_scores)
    if max_score > 0:
         # Normalize slightly conservatively to maintain relative differences
         normalized_relevance = relevance_scores / (max_score + 1e-10)
    else:
         normalized_relevance = relevance_scores
    
    # Calculate pairwise similarities between all candidates
    sim_matrix = cosine_similarity_matrix(vectors, vectors)
    
    num_candidates = len(candidate_ids)
    selected_indices = []
    unselected_indices = list(range(num_candidates))
    
    # Iteratively select candidates
    for _ in range(min(limit, num_candidates)):
        if not selected_indices:
            # First item is purely the most relevant one
            best_idx = unselected_indices[np.argmax(normalized_relevance[unselected_indices])]
        else:
            # Calculate max similarity to already selected items for each unselected item
            # sim_matrix[unselected_indices][:, selected_indices] gets the subset of similarities
            max_sim_to_selected = np.max(sim_matrix[np.ix_(unselected_indices, selected_indices)], axis=1)
            
            # Calculate MMR score
            # score = (1 - lambda) * relevance - lambda * redundancy
            mmr_scores = (1.0 - diversity_penalty) * normalized_relevance[unselected_indices] - \
                         diversity_penalty * max_sim_to_selected
            
            # Find the index with the highest MMR score
            best_local_idx = np.argmax(mmr_scores)
            best_idx = unselected_indices[best_local_idx]
            
        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)
        
    # Build final result
    results = [
        (candidate_ids[idx], candidate_scores[idx]) # Keep original Qdrant scores
        for idx in selected_indices
    ]
    
    return results

"""Markdown chunking utilities for semantic search.

This module provides intelligent chunking of markdown documents that respects
markdown structure (headers, code blocks) while maintaining configurable
chunk sizes and overlaps.
"""

import re
from typing import List, Dict, Any


def chunk_markdown(
    content: str, chunk_size: int = 500, overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Chunk markdown content intelligently, respecting structure.

    This function chunks markdown text while:
    - Preserving code blocks (don't split them)
    - Respecting headers (prefer chunking at headers)
    - Maintaining configurable chunk size and overlap
    - Preserving context across chunks

    Args:
        content: The markdown content to chunk
        chunk_size: Target chunk size in tokens (approximate, using character count)
        overlap: Number of tokens to overlap between chunks

    Returns:
        List of dictionaries with chunk information:
        - 'content': The chunk text
        - 'start_pos': Starting position in original content
        - 'end_pos': Ending position in original content
        - 'chunk_index': Index of this chunk (0-based)
    """
    if not content:
        return []

    # Approximate tokens: roughly 4 characters per token
    char_size = chunk_size * 4
    char_overlap = overlap * 4

    chunks = []
    current_pos = 0
    chunk_index = 0

    # Split by code blocks first to preserve them
    code_block_pattern = r"```[\s\S]*?```"
    code_blocks = list(re.finditer(code_block_pattern, content))

    while current_pos < len(content):
        # Find the end position for this chunk
        end_pos = min(current_pos + char_size, len(content))

        # If we're not at the end, try to find a good break point
        if end_pos < len(content):
            # Prefer breaking at headers (##, ###, etc.)
            header_pattern = r"\n#{1,6}\s+"
            header_match = re.search(
                header_pattern, content[current_pos : end_pos + 100]
            )
            if header_match:
                # Break at the header
                end_pos = current_pos + header_match.start()
            else:
                # Try breaking at paragraph boundaries (double newline)
                para_match = re.search(r"\n\n+", content[end_pos - 200 : end_pos + 100])
                if para_match:
                    # Adjust end_pos to the paragraph break
                    end_pos = end_pos - 200 + para_match.end()
                else:
                    # Try breaking at sentence boundaries
                    sentence_match = re.search(
                        r"[.!?]\s+", content[end_pos - 100 : end_pos + 50]
                    )
                    if sentence_match:
                        end_pos = end_pos - 100 + sentence_match.end()
                    else:
                        # Last resort: break at word boundary
                        word_match = re.search(
                            r"\s+", content[end_pos - 50 : end_pos + 50]
                        )
                        if word_match:
                            end_pos = end_pos - 50 + word_match.end()

        # Check if we're in the middle of a code block
        in_code_block = False
        for cb_match in code_blocks:
            if cb_match.start() < end_pos < cb_match.end():
                # Extend to end of code block
                end_pos = cb_match.end()
                in_code_block = True
                break

        # Extract chunk content
        chunk_content = content[current_pos:end_pos].strip()

        # Only add chunk if it's meaningful (at least 100 chars to avoid tiny fragments)
        if chunk_content and len(chunk_content) >= 100:
            chunks.append(
                {
                    "content": chunk_content,
                    "start_pos": current_pos,
                    "end_pos": end_pos,
                    "chunk_index": chunk_index,
                }
            )
            chunk_index += 1

        # Move to next chunk with overlap
        if end_pos >= len(content):
            break

        # Calculate next start position with overlap
        # Ensure we make meaningful progress (at least 50% of chunk size)
        min_progress = char_size // 2
        next_start = end_pos - char_overlap
        if next_start <= current_pos:
            # Ensure we make progress
            next_start = current_pos + min_progress
        elif (next_start - current_pos) < min_progress:
            # If overlap would create too small a step, ensure minimum progress
            next_start = current_pos + min_progress

        current_pos = next_start

    return chunks

"""Aho-Corasick multi-pattern search with trie, failure, and output links."""

from collections import deque


def aho_corasick_search(text: str, patterns: list[str]) -> tuple[list[tuple[int, int]], int, int]:
    """Find all pattern occurrences in O(n + total pattern length + z) time."""
    children: list[dict[str, int]] = [{}]
    failure = [0]
    outputs: list[list[int]] = [[]]
    output_link = [-1]

    for pattern_index, pattern in enumerate(patterns):
        if not pattern:
            raise ValueError("patterns must not contain an empty string")
        node = 0
        for character in pattern:
            next_node = children[node].get(character)
            if next_node is None:
                next_node = len(children)
                children[node][character] = next_node
                children.append({})
                failure.append(0)
                outputs.append([])
                output_link.append(-1)
            node = next_node
        outputs[node].append(pattern_index)

    queue = deque()
    for child in children[0].values():
        queue.append(child)

    while queue:
        parent = queue.popleft()
        for character, child in children[parent].items():
            fallback = failure[parent]
            while fallback and character not in children[fallback]:
                fallback = failure[fallback]
            failure[child] = children[fallback].get(character, 0)
            suffix = failure[child]
            output_link[child] = suffix if outputs[suffix] else output_link[suffix]
            queue.append(child)

    matches_by_pattern: list[list[int]] = [[] for _ in patterns]
    comparisons = 0
    node = 0
    for text_index, character in enumerate(text):
        while children[node].get(character) is None and node:
            node = failure[node]
            comparisons += 1
        next_node = children[node].get(character)
        if next_node is not None:
            node = next_node
            comparisons += 1

        output_node = node
        while output_node != -1:
            for pattern_index in outputs[output_node]:
                matches_by_pattern[pattern_index].append(text_index - len(patterns[pattern_index]) + 1)
            output_node = output_link[output_node]

    starts: dict[int, list[int]] = {}
    for pattern_index, positions in enumerate(matches_by_pattern):
        for start in positions:
            starts.setdefault(start, []).append(pattern_index)
    matches = []
    for start in range(len(text)):
        for pattern_index in starts.get(start, []):
            matches.append((start, pattern_index))
    return matches, comparisons, len(children)

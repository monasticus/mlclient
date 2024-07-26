from __future__ import annotations

INPUT_DELIMITER = "|"


def parse_step_input(
    step_input: str,
) -> str | list[dict]:
    lines = step_input.split("\n")
    delimiters_count = lines[0].count(INPUT_DELIMITER)
    is_table = delimiters_count > 0
    if not is_table:
        return step_input

    return _parse_step_input_table(lines, delimiters_count)


def _parse_step_input_table(
    input_lines: list[str],
    delimiters_count: int,
) -> list[dict]:
    headings = [cell.strip() for cell in input_lines[0].split(INPUT_DELIMITER)][1:-1]
    rows = []
    for line in input_lines[1:]:
        if line.count(INPUT_DELIMITER) != delimiters_count:
            msg = (
                f"Incorrect number of columns at line: [{line}]! "
                f"Expected: [{delimiters_count}], got: [{line.count(INPUT_DELIMITER)}]",
            )
            raise ValueError(msg)
        cells = [cell.strip() for cell in line.split(INPUT_DELIMITER)][1:-1]
        row = {heading: cells[i] for i, heading in enumerate(headings)}
        rows.append(row)

    return rows

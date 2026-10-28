"""Read resource spellings used by this project's CSS guard, not a CSS parser.

Names and URL/string values decode CSS escapes independently. A global decode
would turn escaped quotes into delimiters and text in strings into resources.
"""

_SPACE = ' \t\n'
_HEX = '0123456789abcdefABCDEF'


def _escape(source, index):
    """Consume the backslash at index (CSS Syntax 3, escaped code point)."""
    index += 1
    if index == len(source):
        return '\ufffd', index
    if source[index] in _HEX:
        end = index
        while end < len(source) and end - index < 6 and source[end] in _HEX:
            end += 1
        number = int(source[index:end], 16)
        value = chr(number) if number and number <= 0x10ffff and not 0xd800 <= number <= 0xdfff else '\ufffd'
        if end < len(source) and source[end] in _SPACE:
            end += 1
        return value, end
    if source[index] == '\n':
        return '', index + 1
    return source[index], index + 1


def _string(source, index):
    quote = source[index]
    result = []
    index += 1
    while index < len(source):
        character = source[index]
        if character == quote:
            return ''.join(result), index + 1
        if character == '\n':
            return ''.join(result), index
        if character == '\\':
            value, index = _escape(source, index)
            result.append(value)
        else:
            result.append(character)
            index += 1
    return ''.join(result), index


def _name(source, index):
    result = []
    while index < len(source):
        character = source[index]
        if character.isalnum() or character in '-_' or ord(character) >= 128:
            result.append(character)
            index += 1
        elif character == '\\' and index + 1 < len(source) and source[index + 1] != '\n':
            value, index = _escape(source, index)
            result.append(value)
        else:
            break
    return ''.join(result), index


def _space_comments(source, index):
    while index < len(source):
        if source[index] in _SPACE:
            index += 1
        elif source.startswith('/*', index):
            end = source.find('*/', index + 2)
            index = len(source) if end < 0 else end + 2
        else:
            break
    return index


def css_resources(css):
    """Yield decoded url(...) and quoted @import values outside prose strings.

    Covers the resource notation accepted by this project. This intentionally
    does not validate the complete CSS grammar or decide whether rules apply.
    """
    source = css.replace('\r\n', '\n').replace('\r', '\n').replace('\f', '\n').replace('\0', '\ufffd')
    index = 0
    while index < len(source):
        next_index = _space_comments(source, index)
        if next_index != index:
            index = next_index
            continue
        character = source[index]
        if character in '\"\'':
            _, index = _string(source, index)
            continue
        if character == '@':
            name, index = _name(source, index + 1)
            if name.lower() == 'import':
                index = _space_comments(source, index)
                if index < len(source) and source[index] in '\"\'':
                    value, index = _string(source, index)
                    yield value
            continue
        name, end = _name(source, index)
        if end == index:
            index += 1
            continue
        index = end
        if name.lower() != 'url' or index == len(source) or source[index] != '(':
            continue
        index = _space_comments(source, index + 1)
        if index < len(source) and source[index] in '\"\'':
            value, index = _string(source, index)
        else:
            result = []
            while index < len(source) and source[index] != ')':
                if source[index] == '\\':
                    value, index = _escape(source, index)
                    result.append(value)
                else:
                    result.append(source[index])
                    index += 1
            value = ''.join(result).strip()
        yield value

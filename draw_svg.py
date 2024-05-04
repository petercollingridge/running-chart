class SVG_Element:
    """ Generic element with attributes and potential child elements.
        Outputs as <tag attribute dict> child </tag>."""

    indent = 4

    def __init__(self, tag, attributes=None, child=None):
        self.tag = tag
        self.attributes = attributes or {}
        self.children = {'root': []}
        self.child_order = ['root']

        if child is not None:
            self.children['root'] = [str(child)]

    def addChildElement(self, tag, attributes=None, child=None):
        """
            Create an element with given tag and atrributes,
            and append to self.children.
            Returns the child element.
        """

        child = SVG_Element(tag, attributes, child)
        self.children.append(child)
        return child

    def add(self, tag, attributes=None, child=None):
        child = SVG_Element(tag, attributes, child)
        self.children['root'].append(child)
        return child

    def rect(self, x, y, width, height, **kwargs):
        kwargs['x'] = x
        kwargs['y'] = y
        kwargs['width'] = width
        kwargs['height'] = height

        child = SVG_Element('rect', kwargs)
        self.children.append(child)

        return child

    def circle(self, x, y, r, **kwargs):
        kwargs['cx'] = x
        kwargs['cy'] = y
        kwargs['r'] = r

        child = SVG_Element('circle', kwargs)
        self.children.append(child)

        return child

    def output(self, nesting=0):
        indent = ' ' * nesting * self.indent
        svg_string = f'{indent}<{self.tag}'

        for key, value in self.attributes.items():
            if key == 'classname':
                key = 'class'
            svg_string += f' {key}="{value}"'

        child_string = ''
        new_line = False

        for child_name in self.child_order:
            try:
                child = self.children[child_name]
            except KeyError:
                print(f'No child with name {child_name}')
                continue

            if isinstance(child, SVG_Element):
                child_string += '\n' + child.output(nesting + 1)
                new_line = True
            else:
                child_string += child
    
        if child_string:
            svg_string += '>' + child_string

            if new_line:
                svg_string += '\n' + indent

            svg_string += f'</{self.tag}>'

        else:
            # Self closing tag
            svg_string += '/>'

        return svg_string


class SVG(SVG_Element):
    """ SVG element with style element and output that includes XML document string. """

    def __init__(self, attributes=None):
        SVG_Element.__init__(self, 'svg', attributes)
        self.attributes['xmlns'] = 'http://www.w3.org/2000/svg'

        style_element = SVG_Style_Element()
        self.children['style'] = [style_element],
        self.child_order = ['style', 'root']

        self.style_dict = style_element.children

    def addStyle(self, element, attributes):
        """
            Add style to element in self.style.children using a dictionary in
            form {selector: value}
        """

        if element not in self.style_dict:
            self.style_dict[element] = {}
        self.style_dict[element].update(attributes)

    def outputToFile(self, filename):
        """ Prints output to a given filename. Add a .svg extenstion if not given. """

        import os
        if not os.path.splitext(filename)[1] == '.svg':
            filename += '.svg'

        with open(filename, 'w') as f:
            f.write(self.output())

    def write(self, filename=None):
        """ Write output to file if given a filename, otherwise return output as a string. """

        if not filename:
            return self.output()
        else:
            self.outputToFile(filename)


class SVG_Style_Element(SVG_Element):
    def __init__(self):
        self.children = {}

    def output(self, nesting=0):
        if not self.children:
            return ''

        style_string = '\n<style>\n'

        for element, style in self.children.items():
            style_string += '  %s {\n' % element

            for key, value in style.items():
                style_string += f'    {key}: {value};\n'
            style_string += '  }\n'

        style_string += '  </style>\n'

        return style_string

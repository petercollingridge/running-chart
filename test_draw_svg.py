from draw_svg import SVG

svg = SVG()
svg.add_section('section-1')
svg.add_section('section-2')

section_1 = svg.get_section('section-1')
section_2 = svg.get_section('section-2')

section_2.rect(50, 50, 80, 80, fill='green', opacity=0.5)
section_1.rect(0, 0, 100, 100, fill='red')

svg.write("test")

# Design Tokens

Design tokens are settings that can be shared easily between systems. They are
stored in a readable format like [YAML](https://en.wikipedia.org/wiki/YAML).
Settings like typography, general spacing/padding, and color are common.
Configuration of different themes are also done here.

More articles about design tokens:

- [EightShapes - Tokens in Design Systems](https://medium.com/eightshapes-llc/tokens-in-design-systems-25dd82d58421)
- [CSS-Tricks - What Are Design Tokens?](https://css-tricks.com/what-are-design-tokens/)

## Colors

Color naming convention inspired by [Naming Conventions for colors - by Kevin Mack](http://codepen.io/nicetransition/pen/QjwbRg).

| Name      | Modifier | Usage                                                                                   |
| --------- | -------- | --------------------------------------------------------------------------------------- |
| Primary   | No       | Main color.                                                                             |
| Secondary | No       | Optional color and usually different from the primary color.                            |
| Tertiary  | No       | Another optional color that would go along with the other primary and secondary colors. |
| Dark      | Yes      | Should be dark gray or dark neutral colors low in saturation.                           |
| Light     | Yes      | Should be light gray or light neutral colors low in saturation.                         |
| Accent    | Yes      | Used sparingly to draw attention.                                                       |
| Error     | No       | For error messages and warnings; usually red.                                           |

Use of colors loosely follow [Material Design guidelines](https://www.material.io/design/color/).

Color aliases are defined in [color.yaml file](./color.yaml).

### Tools

Contrast color checker:
https://webaim.org/resources/contrastchecker/

Material Design site also has some color tools.
https://www.material.io/design/color/

## Reference

Spec
https://github.com/salesforce-ux/theo

| Category            | Friendly Name          |
| ------------------- | ---------------------- |
| spacing             | Spacing                |
| sizing              | Sizing                 |
| font                | Fonts                  |
| font-style          | Font Styles            |
| font-weight         | Font Weights           |
| font-size           | Font Sizes             |
| line-height         | Line Heights           |
| font-family         | Font Families          |
| border-style        | Border Styles          |
| border-color        | Border Colors          |
| radius              | Radius                 |
| border-radius       | Border Radii           |
| hr-color            | Horizontal Rule Colors |
| background-color    | Background Colors      |
| gradient            | Gradients              |
| background-gradient | Background Gradients   |
| drop-shadow         | Drop Shadows           |
| box-shadow          | Box Shadows            |
| inner-shadow        | Inner Drop Shadows     |
| text-color          | Text Colors            |
| text-shadow         | Text Shadows           |
| time                | Time                   |
| media-query         | Media Queries          |

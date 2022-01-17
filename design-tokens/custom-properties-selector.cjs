/*
This file in the parent directory design-tokens was generated from the design-tokens directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.
*/

module.exports = (theo) => {

  theo.registerFormat(
    "custom-properties-selector.css",
    `{{#each props as |prop|}}
{{#if prop.comment}}
{{{trimLeft (indent (comment (trim prop.comment)))}}}
{{/if}}
{{#if prop.selector~}}
  {{prop.selector}}
{{~^~}}
  :root
{{~/if~}}
{
  --designtoken-{{prop.name}}: {{#eq prop.type "string"}}"{{/eq}}{{{prop.value}}}{{#eq prop.type "string"}}"{{/eq}};
}
{{/each}}`
  );
};

/* TODO: First part of prop.name should match prop.category
{{capitalize (camelcase prop.category)}}-
The prop.name needs to be unique across all design tokens or the proceeding one
is replaced.
*/

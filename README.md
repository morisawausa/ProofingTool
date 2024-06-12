# Proofing Tool

This Glyphs Plugin helps you output proofs directly from Glyphs. The plugin focuses on generating form comparison proofs in two forms: [waterfall] and [paragraph] view. It currently isn’t intended to robustly proof typesetting and opentype features, but these capabilities may be added at some point in the future.

This tool can be used to format and output paragraphs and waterfalls of text set in an in-progress typeface from directly inside of Glyphs 3. It should help you quickly format for proofing use without needing to export font binaries, deal with font caching, or open InDesign. We made this tool with the hope that it might reduce the annoyance of producing proofs for in-progress work, for internal review.

## Prerequisites:

1. You must have the following installed this to work. Install them via the Plugin Manager on Glyphs.
- Modules: Vanilla and Python
- Plugin: [DrawBot](https://github.com/schriftgestalt/DrawBotGlyphsPlugin)

2. Open a glyphs file. The tool will use your currently selected file to generate the proof.

3. Make sure that you have `exports` setup in your Font Information.
 

### On Setting up Exports
⚠️ The tool, by default, will use the `Style Name` field on the exports tab to setup the list of available instances.

 However, in cases of multi-axes variable font, you may have duplicate `Style Name` entries across instances to support style-linked static font & VF exports from the same Glyphs file. In this case, the exports list will concatenate the default values in `Typographic Family Names` and `Typographic Style Names` (if specified, falling back to the `Style Name`.) 

This means that the proof templates will be setup with a specific family name, such as “Dispatch 2 Compressed ExtraLight” and won’t work for other typefaces. If re-using the template for another typeface, I recommend editing the template file in a text-editor to find-and-replace the Typographic Family Name. (We may be able to better extract style names by using more complex processing of those fields, but setting up the names in the Glyphs panel for production export can be tricky business, so let us know if you have any recommendations here.)

**If there are duplicate `Style Name` entries but no `Typographic Family/Syle Names` entries, there will be missing instances in the dropdown field selection.**


## Using the Tool

1. Load / Select a Template

- In order to proof the typeface, you must first select a proofing template. The window will load any previously-loaded templates in the window. You can load additional template files or remove them from the view with the `+` / `-` buttons.
More on the [templates] below.

- If there are no previously-loaded templates, it will load the demo template file, which outputs the basic Latin alphabet in the Regular style at 48pts — so if you do not have a `Regular`, you won’t see anything in the proofing window. 

2. Review / edit the template as needed.

- To adjust the template, click on the `Edit` tab above. See [Creating and Editing Templates]

3. Click the `❇️  Proof` button. This will apply the template with any additional edits.

4. Review the `Proof Name`. You can now:

`📋 Save As Template` Save the current template as a new `.json` template file. Note: the Proof Name should be unique and not a duplicate of an existing template. (To do: support saving template changes to currently selected template, rather than always forcing a Save As.)

`📄 Save PDF` Save a copy of the generated proof to your computer

`🖨 Print Proof"`Send the PDF to your printer


⚠️ If you have a lot of instances, generating the proof can take some time as instances are reinterpolated. To help with this, there is a `Re-export Instances` checkbox to keep checked if additional instances need to be proofed, or if you change the shapes of a master. Keep this unchecked for simple layout changes with no changes to the instances. (To do: this optimization may be automated down the line.)

## Creating and Editing Templates: UI Option

The `Edit` tab allows you to set up your proof.

![View of the tool showing the edit view with a waterfall mode](docs/sample_waterfall_edit.png)

### Styles and Sizes
The first section lets you select the instances and point sizes you’d like to compare. Each line in the list on the edit view corresponds to a style and point-size in your proof. 

Use the `+` and `-` buttons to add / remove instances to this list.
(In case you missed it, see [Setting up Exports] on caveats on instance naming.)

### Glyph Selection
You’ll then choose which glyphs you’ll want in the proof. You have 3 options:

- `Template Glyphs` these are the glyphs specified in the `glyphs` key of the template file

- `Font View` this option will use the glyphs currently selected in the Font View of the Glyphs app

- `Edit View` this option will use the glyphs currently displayed in the Edit View of the Glyphs app

### Proofing Mode

- `Waterfall`

**Waterfall** proofs are for line-by-line comparisons. A waterfall proof prints _a single line of text_ per selected style, with each line of text containing the same set of glyphs.

![Image of a waterfall-style proof in the proofing tool window](./docs/sample-waterfall.png)

The proof in the above image sets the character set of a type family in a waterfall style. The text is broken up into blocks of a single line per style or size (this image shows them all at 24pt, but this can also be set up where each line is a different size). Any text that doesn’t fit into the line is pushed to the next block. If the block doesn’t fit entirely on the page, the entire block is shifted onto the next page.

A key feature of the waterfall proof is that it *puts the same set of characters on each line*. This can be useful for comparing interpolation results across a family, checking alignment of diacritic placements, or any stray spacing errors.

- `Paragraph`

A **Paragraph** proof are for block-by-block comparisons. A paragraph proof will output the entire set of specified glyphs together for each selected style.

![Image of a paragraph-style proof in the proofing tool window](./docs/sample-paragraph.png)

In the paragraph proof, the entire text is displayed in a single paragraph, before we move on to the next style. (As you can tell from the above image, the Paragraph proof is best suited to longer chunks of text.)

A key feature of the paragraph proof is that it *full blocks of text* across styles. This can be especially useful for comparing textures with specific glyphs generated from the Edit View. Depending on where you are in the type design process, it might be a set of [word-o-mat]()-generated paragraph of control characters, a set of spacing strings, stylistic alternates, or sample texts of a particular language.

### Layout

These settings help you adjust the spacing in and around the blocks of text in the proof. All of the measurements in this section are specified in pixels. (At some point, we may change these into more typographic units). 

`Gaps` settings control spacing within the proof content. `Line` refers to the space inserted between each line of text; `Block` refers to the space inserted between groups of lines. 

In Waterfall mode, the `Block` is a set of lines, one for each specified style, displaying the same set of glyphs that would fit on one line.

![Layout settings for waterfall mode](./docs/layoutsettings_waterfall.png)


In Paragraph mode, the `Block` is effectively be the paragraph of all text for specified style.

![Layout settings for paragraph mode](./docs/layoutsettings_paragraph.png)


Margins of the document is the space around the lines of glyphs. Note: a larger `right` and `bottom` margin is recommended, especially with the footer being inserted at the bottom.

Currently, the Editing UI isn’t the most user-friendly. For example, you can’t drag-and-drop to reorder styles, or change all the sizes of each style at once. For significant edits to your templates, we recommend using a Text Editor to directly edit the template data files.

## Creating and Editing Templates: Text Editor Option

This tool uses a JSON-based template format to store proof configurations on a pre-project basis. You can version control these JSON files together with the rest of your typeface sources, if you wish. The intention here is to provide a way of quickly rendering proofs, without having to configure the tool each time you want to use it.

Personally, I think the easiest thing to do is to adapt the `data/demo.json` file in this respository to suit the needs of your font project. You can keep the edited file in this repository and use it while you work, or copy it into your font project directory, for posterity. The tool will automatically load the contents of previously-opened data files.

The rest of this section will walk you through the template syntax. Note that the JSON format is very strict, so it won’t work if there’s even a single syntax error; if you are new to JSON-editing, I recommend double-checking that your file is error-free through Online JSON validators. (To do: allow UI to enable DEBUG mode for template errors)

At the root, the template JSON looks like this:

```js
{
  "name": "My Proof Name",
  "proof": { ... } // configuration for the proof
  "lines": [ ... ] // different styles to render...
  "glyphs": [ ... ] // list of glyph names in the file as strings.
}
```


You may want to set up some standard template proofs corresponding to various stages of your design process. But there are often variations with each font: they may have slightly different glyph sets to render, be drawn for different optical sizes, or have different master names, so it’s often helpful to be able to make custom templates for each project as well.

Let’s look at each of the keys in the JSON structure. The `"name"` key, obviously, is the name of the proof. It gets rendered at the bottom of the document and can be whatever you want.

The `"proof"` key contains all of the layout details for rendering the proof. It looks like the following JSON structure:

```js
{
  ...
  "proof": {
    /**
     * These are the page margins, in pixels. for ease of working with DrawBot,
     * the calculations for layout and rendering are done in pixel space. So far,
     * this hasn't been a huge issue for us, but we may convert to a different
     * unit system at some point.
     */
    "margins": {
      "left": 20,
      "right": 50,
      "top": 20,
      "bottom": 50
    },
    /**
     * These are padding values (also in pixels) to put in between lines and
     * blocks. A line is a single line of glyphs running the length of the page.
     * a block is one contiguous block of glyphs. In waterfall mode, a block is
     * one line of glyphs across each style that you're rendering. In paragraph
     * mode, a block is one entire run of glyphs – paragraph – in a single
     * style. Line padding is added between each line, block padding is added
     * after each block.
     */
    "padding": {
      "block": 20,
      "line": 30
    },
    /**
     * This is the rendermode: either "waterfall" or "paragraphs"
     */
    "mode": "waterfall"
  },
  ...
}
```

The `"lines"` key specifies which styles to render, at which point size, and in which order. Styles are pulled from the instance list by default. If there are no instances, Styles are pulled from the masters list.

```js
{
  ...
  /**
   * Individual lines go in this array.
   */
  "lines": [
    /**
     * Each element in the lines array should be an object with a "style" and
     * "size" key. The style key should be the name of a master in the typeface.
     * The "size" is an integer specifying the pointsize to render that master
     * at. You can have as many of these as you want.
     */
    {"style": "Extra Light", "size": 50},
    {"style": "Regular", "size": 50},
    {"style": "Black", "size": 50},
    ...
  ],
  /**
   * This key is optional. Sometimes, you just want to render the same size
   * across a range of styles. In this case, you can add a default size here,
   * and then just specify the styles in the lines array.
   */
  "size": 50,
  /**
   * This key is optional. Sometimes, you just want to render the same style
   * at a range of sizes. In this case, you can add a default style here,
   * and then just specify the sizes in the lines array.
   */
  "style": "Regular",
  ...
}
```

Finally, the `"glyphs"` key specifies an in-order sequence of glyphs to render. This is fairly straightforward: just an array of glyph names as strings, just as `Glyphs.app` would expect them (nothing fancy, no leading `/`, etc. If you want the glyph `Aacute` to render, put `"Aacute"` in this list).

👉 An easy way to get a set of glyphs is to select them in Font View, right click, then `Copy Glyph Names > Python List`. Remove the last trailing `,` and wrap the list in `[]`, and assign it to the `"glyphs"` key. Note: if selecting glyphs from the Edit View, this Copy Glyph Names method will *not* preserve line breaks displayed. To specify a line break in the proof, add `"newGlyph"` in the glyphs list. (Line breaks are detected automatically when extracting glyphs from the Edit View using the Proofing Tool UI.)

## Issues
We’ve logged a number of other known issues on the repo. Feel free to leave any additional issues as you encounter them. Thanks!


## Installation

At this moment, the tool works as a Glyphs.app script. To install the tool:

1. Install the DrawBot plugin using the built-in Plugin Manager in Glyphs.app. This tool uses drawbot to prepare proofs, so it requires you to have that library installed and available to Glyphs.app.

2. Clone this git repository into your Glyphs.app Scripts directory. This is the same folder where your `_GlyphsScripts` folder lives, for example. It's usually somewhere like `~/Library/Application Support/Glyphs/Scripts`. (The `~` is your user’s home folder, something like `/Users/nic`, for example).

3. Restart Glyphs.

## About


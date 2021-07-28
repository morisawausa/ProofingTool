# Occupant Proofing Tool

This Glyphs Plugin helps you output proofs directly from Glyphs. The plugin focuses on generating form comparison proofs like waterfalls, rather than proofs that help you proof typesetting and opentype features. These capabilities may be added at some point in the future.

For a items on our roadmap, look at [this document](https://docs.google.com/document/d/1z0BD3hXVslzn5acJ_5KomH_WkwnMeQ9gEiJh3z79fHE/edit).

**⚠️ NOTE: ⚠️** This application was recently converted to render instances, rather than masters. If you don't have any instances in your font, the tool *might* not work.

**⚠️ NOTE: ⚠️** Using instance geometry requires instances to be re-interpolated when the script starts up. Because of this, if you have a lot of instances, starting the proofing tool can take some time as instances are reinterpolated. At some point I'll optimize this so that it only reinterpolates the instances you need.

## Templates

This tool uses a JSON-based template format to store proof configurations on a pre-project basis. You can version control these JSON files together with the rest of your typeface sources, if you wish. The intention here is to provide a way of quickly rendering proofs, without having to configure the tool each time you want to use it.

Personally, I think the easiest thing to do is to directly edit the `data/demo.json` file in this respository to suit the needs of your project. You can keep the edited file in this repository and use it while you work, or copy it into your font project directory, for posterity. The tool will automatically load the contents of the `data/` directory when it starts up, so you can add however many proof templates you want to this folder while working, and they'll load on startup. (You can also open any json file in the tool while it's running, but these files aren't remembered between runs of the tool. For that reason, it's more convenient to just drop files in the `demo` folder directly and skip the load step.)

The rest of this section will walk you through the template syntax. Hopefully, it's pretty straightforward.

At the root, the template JSON looks like this:

```js
{
  "name": "My Proof's Name",
  "proof": { ... } // configuration for the proof
  "lines": [ ... ] // different styles to render...
  "glyphs": [ ... ] // list of glyph names in the file as strings.
}
```

Because each font may want slightly different glyph sets to render, and because each font has different or slightly different master names, it's best to make custom templates for each project.

Let's look at each of the keys in the JSON structure. The `"name"` key, obviously, is the name of the proof. It gets rendered at the bottom of the document and can be whatever you want.

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

That's about it. There may be a few bugs in the the template IO system, so if you encounter something like a value in the `"proof"` key not being loaded properly, go ahead and leave an issue on this repo. Thanks.

## Installation

At this moment, the tool works as a Glyphs.app script. To install the tool:

1. Install the DrawBot plugin using the built-in Plugin Manager in Glyphs.app. This tool uses drawbot to prepare proofs, so it requires you to have that library installed and available to Glyphs.app.

2. Clone this git repository into your Glyphs.app Scripts directory. This is the same folder where your `_GlyphsScripts` folder lives, for example. It's usually somewhere like `~/Library/Application Support/Glyphs/Scripts`. (The `~` is your user's home folder, something like `/Users/nic`, for example).

3. Restart Glyphs.

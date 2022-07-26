/**
 * Converts an RGB color value to HSL. Conversion formula
 * adapted from http://en.wikipedia.org/wiki/HSL_color_space.
 * Assumes r, g, and b are contained in the set [0, 255] and
 * returns h, s, and l in the set [0, 1].
 *
 * @param   {number}  r       The red color value
 * @param   {number}  g       The green color value
 * @param   {number}  b       The blue color value
 * @return  {Array}           The HSL representation
 */
export function rgbToHsl(r16, g16, b16) {
  let r = parseInt(r16, 16) / 255.0;
  let g = parseInt(g16, 16) / 255.0;
  let b = parseInt(b16, 16) / 255.0;
  let max = Math.max(r, g, b);
  let min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  let l = (max + min) / 2.0;
  if (max === min) {
    h = s = 0; // achromatic
  } else {
    let d = max - min;
    s = l > 0.5 ? d / (2.0 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
  }
  // Convert to degrees
  h = h * 60.0;
  if (h < 0) {
    h = h + 360;
  }
  // Convert to percentage
  s = s * 100;
  l = l * 100;
  return [h, s, l];
}
export function getTimePassed(secondsFromNow) {
  let timePassed = "";
  if (secondsFromNow < 2) {
    timePassed = "1 second";
  } else if (secondsFromNow < 60) {
    timePassed = `${secondsFromNow} seconds`;
  } else if (secondsFromNow < 2 * 60) {
    timePassed = "1 minute";
  } else if (secondsFromNow < 60 * 60) {
    timePassed = `${Math.floor(secondsFromNow / 60)} minutes`;
  } else if (secondsFromNow < 60 * 60 * 2) {
    timePassed = "1 hour";
  } else if (secondsFromNow < 60 * 60 * 24) {
    timePassed = `${Math.floor(secondsFromNow / 60 / 60)} hours`;
  } else if (secondsFromNow < 60 * 60 * 24 * 2) {
    timePassed = "1 day";
  } else {
    timePassed = `${Math.floor(secondsFromNow / 60 / 60 / 24)} days`;
  }
  return timePassed;
}

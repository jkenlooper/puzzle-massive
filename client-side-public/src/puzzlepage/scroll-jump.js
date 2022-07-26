import "./jump-point-marker.css";
export default () => {
  // TODO: When setting a jump point attach a number to the DOM at that point
  // let _element = element
  let jumpPoints = {};
  let jumps = [];
  init();
  function init() {
    document.addEventListener("keydown", (event) => {
      if (event.defaultPrevented) {
        return; // Do nothing if the event was already processed
      }
      switch (event.key) {
        // Standard gaming style movement
        case "w":
          scrollUp(1);
          break;
        case "a":
          scrollLeft(1);
          break;
        case "s":
          scrollDown(1);
          break;
        case "d":
          scrollRight(1);
          break;
        case "W":
          scrollUp(2);
          break;
        case "A":
          scrollLeft(2);
          break;
        case "S":
          scrollDown(2);
          break;
        case "D":
          scrollRight(2);
          break;
        // Back
        case "z":
          scrollBack();
          break;
        // Record jump points 1-9
        case "!":
          setJumpPoint("1");
          break;
        case "@":
          setJumpPoint("2");
          break;
        case "#":
          setJumpPoint("3");
          break;
        case "$":
          setJumpPoint("4");
          break;
        case "%":
          setJumpPoint("5");
          break;
        case "^":
          setJumpPoint("6");
          break;
        case "&":
          setJumpPoint("7");
          break;
        case "*":
          setJumpPoint("8");
          break;
        case "(":
          setJumpPoint("9");
          break;
        case ")":
          setJumpPoint("0");
          break;
        case "1":
          scrollToJumpPoint("1");
          break;
        case "2":
          scrollToJumpPoint("2");
          break;
        case "3":
          scrollToJumpPoint("3");
          break;
        case "4":
          scrollToJumpPoint("4");
          break;
        case "5":
          scrollToJumpPoint("5");
          break;
        case "6":
          scrollToJumpPoint("6");
          break;
        case "7":
          scrollToJumpPoint("7");
          break;
        case "8":
          scrollToJumpPoint("8");
          break;
        case "9":
          scrollToJumpPoint("9");
          break;
        case "0":
          scrollToJumpPoint("0");
          break;
        default:
          return;
      }
    });
  }
  function setJumpPoint(jumpPointId) {
    jumpPoints[jumpPointId] = [window.scrollX, window.scrollY];
    const markerId = "jump-point-marker-" + jumpPointId;
    let marker = document.getElementById(markerId);
    // Create marker element if not there
    if (!marker) {
      marker = document.createElement("div");
      marker.innerText = jumpPointId;
      marker.setAttribute("id", markerId);
      marker.classList.add("pm-JumpPointMarker");
      document.body.appendChild(marker);
    }
    // Set new position of marker
    marker.style.left = jumpPoints[jumpPointId][0] + "px";
    marker.style.top = jumpPoints[jumpPointId][1] + "px";
  }
  function scrollToJumpPoint(jumpPointId) {
    if (jumpPoints[jumpPointId]) {
      // Record previous scroll position in the jumps array
      jumps.push([window.scrollX, window.scrollY]);
      if (jumps.length > 50) {
        jumps.shift();
      }
      window.scrollTo.apply(window, jumpPoints[jumpPointId]);
    }
  }
  function scrollBack() {
    let jumpPoint = jumps.pop();
    if (jumpPoint) {
      window.scrollTo.apply(window, jumpPoint);
    }
  }
  function scrollDown(scale) {
    window.scrollBy(0, window.innerHeight / scale);
  }
  function scrollUp(scale) {
    window.scrollBy(0, (window.innerHeight / scale) * -1);
  }
  function scrollLeft(scale) {
    window.scrollBy((window.innerWidth / scale) * -1, 0);
  }
  function scrollRight(scale) {
    window.scrollBy(window.innerWidth / scale, 0);
  }
  // No public methods for now
  return {};
};

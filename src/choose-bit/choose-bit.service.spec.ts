import tape from "tape";
import fetchMock from "fetch-mock";
import { ChooseBitService } from "./choose-bit.service";
//import jsdom from "jsdom";

//const { JSDOM } = jsdom;
//const { window } = new JSDOM(`...`);
// or even
//const { document } = new JSDOM(`...`).window;

tape("getBits", (t) => {
  fetchMock.mock("/newapi/choose-bit/", { data: ["test", "frog"] });
  /*
  function mockFetch(url: any) {
    console.log(url);
    return {
      then: function(func: any) {
        func();
      },
    };
  }
   */
  t.plan(2);
  const chooseBitService = new ChooseBitService();
  t.equal(typeof chooseBitService.getBits, "function");

  chooseBitService
    .getBits(10)
    .then((bits) => {
      t.deepEqual(bits, { data: ["test", "frog"] });
    })
    .finally(() => {
      t.end();
    });

  fetchMock.restore();
});

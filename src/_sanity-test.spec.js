import mocha from "mocha";
import chai from "chai";

mocha.suite("Sanity test", () => {
  mocha.test("Chai assert is working", () => {
    const actual = ["ex", "pec", "ted"].join("");
    chai.assert("expected" === actual, "can join an array into a string");
  });
});

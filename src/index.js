/*
Export for use in the webpack.config.js entry configuration.
These are the entry bundles for specific layouts of the site.
*/

module.exports = {
  frontpage: './src/frontpage/index.js',
  docspage: './src/docspage/index.js',
  scorespage: './src/scorespage/index.js',
  puzzlepage: './src/puzzlepage/index.js',
  puzzleuploadpage: './src/puzzleuploadpage/index.js',
  profilepage: './src/profilepage/index.js',
  queuepage: './src/queuepage/index.js',
  adminpuzzlepage: './src/adminpuzzlepage/index.js',
  testpage: './src/testpage/index.js'
  // Other pages would go here
  // other: './src/other.js',
}

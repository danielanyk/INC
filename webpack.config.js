const path = require('path');

module.exports = {
  entry: './apps/static/assets/index.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'apps/static/assets'),
  },
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  resolve: {
    modules: [path.resolve(__dirname, 'node_modules')],
  },
};
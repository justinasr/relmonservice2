module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  assetsDir: 'static/',
  publicPath: process.env.NODE_ENV !== 'production'
    ? '/relmonsvc'
    : '/relmonsvc',
  devServer: {
    logLevel: 'debug'
  },
}

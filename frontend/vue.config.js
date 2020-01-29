const isProd = process.env.NODE_ENV === "production"

module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  publicPath: isProd ? '/relmonsvc' : '',
  assetsDir: 'static/',
  devServer: {
    port: 8003,
    logLevel: 'debug'
  }
}

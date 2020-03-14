<template>
  <v-app>
    <v-app-bar app style="background-color: white;">
      <a href="" style="text-decoration: none; color: rgba(0, 0, 0, 0.87);">
        <v-toolbar-title class="headline">
          <span>RelMon</span>
          <span class="font-weight-light">Service</span>
        </v-toolbar-title>
      </a>
    </v-app-bar>

    <v-content>
      <MainComponent/>
    </v-content>
  </v-app>
</template>

<script>
import MainComponent from './components/MainComponent';

export default {
  name: 'App',
  components: {
    MainComponent,
  },
  data: () => ({
    //
  }),
};
</script>

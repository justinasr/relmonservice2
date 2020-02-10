<template>
  <v-app>
    <v-app-bar app style="background-color: white;">
      <v-toolbar-title class="headline">
        <span>RelMon</span>
        <span class="font-weight-light">Service</span>
      </v-toolbar-title>
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

<template>
  <v-app>
    <v-container>
      <CreateNewRelMonComponent @refetchRelmons="refetchRelmons" ref="createNewRelMonComponent"></CreateNewRelMonComponent>
      <RelMonComponent @editRelmon="editRelmon" @refetchRelmons="refetchRelmons" v-for="relmonData in fetchedData" :key="relmonData.name" :relmonData="relmonData"></RelMonComponent>
    </v-container>
  </v-app>
</template>

<script>
import axios from 'axios'
import RelMonComponent from './RelMonComponent';
import CreateNewRelMonComponent from './CreateNewRelMonComponent';

export default {
  name: 'MainComponent',
  data () {
    return {
      fetchedData: {}
    }
  },
  created () {
    this.refetchRelmons()
  },
  watch: {
  },
  components: {
    RelMonComponent,
    CreateNewRelMonComponent
  },
  methods: {
    editRelmon(relmon) {
      this.$refs.createNewRelMonComponent.startEditing(relmon)
    },
    refetchRelmons() {
      axios.get('api/get_relmons').then(response => {
        this.fetchedData = response.data.data;
      });
    }
  }
}
</script>

<style scoped>
</style>
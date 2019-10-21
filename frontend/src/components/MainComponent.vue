<template>
  <v-app>
    <v-container>
      <CreateNewRelMonComponent ref="createNewRelMonComponent"></CreateNewRelMonComponent>
      <RelMonComponent @editRelmon="editRelmon" v-for="relmonData in fetchedData" :key="relmonData.name" :relmonData="relmonData"></RelMonComponent>
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
      fetchedData: {},
      editingRelmon: undefined
    }
  },
  created () {
    axios.get('/relmonsvc/api/get_relmons').then(response => {
      this.fetchedData = response.data.data;
    });
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
    }
  }
}
</script>

<style scoped>
</style>
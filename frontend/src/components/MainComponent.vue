<template>
  <v-app>
    <v-container>
      <CreateNewRelMonComponent @refetchRelmons="refetchRelmons" :userInfo="userInfo" ref="createNewRelMonComponent"></CreateNewRelMonComponent>
      <RelMonComponent @editRelmon="editRelmon" @refetchRelmons="refetchRelmons" v-for="relmonData in fetchedData" :key="relmonData.name" :relmonData="relmonData" :userInfo="userInfo"></RelMonComponent>
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
      userInfo: {'name': '', 'authorized': false}
    }
  },
  created () {
    this.refetchRelmons();
    this.fetchUserInfo();
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
    },
    fetchUserInfo() {
      let component = this;
      axios.get('api/user').then(response => {
        component.userInfo.name = response.data.fullname;
        component.userInfo.authorized = response.data.authorized_user;
      });
    }
  }
}
</script>

<style scoped>
</style>
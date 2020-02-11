<template>
  <v-app style="background-color: #fafafa">
    <v-container>
      <CreateNewRelMonComponent @refetchRelmons="refetchRelmons" :userInfo="userInfo" ref="createNewRelMonComponent"></CreateNewRelMonComponent>
      <RelMonComponent @editRelmon="editRelmon" @refetchRelmons="refetchRelmons" v-for="relmonData in fetchedData" :key="relmonData.name" :relmonData="relmonData" :userInfo="userInfo"></RelMonComponent>
      <v-row style="line-height: 36px; text-align: center;">
        <v-col class="elevation-3 pa-2 mb-2" style="background: white">
          <v-btn small color="primary" style="float: left" class="ma-1" v-if="page > 0" @click="previousPage()">Previous Page</v-btn>
          <span class="font-weight-light">Page:</span> {{page}}
          <v-btn small color="primary" style="float: right" class="ma-1" v-if="page * pageSize < totalRows" @click="nextPage()">Next Page</v-btn>
        </v-col>
      </v-row>
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
      userInfo: {'name': '', 'authorized': false},
      page: 0,
      totalRows: 0,
      pageSize: 0
    }
  },
  created () {
    let urlParams = Object.fromEntries(new URLSearchParams(window.location.search));
    if (!('page' in urlParams)) {
      this.page = 0;
    } else {
      this.page = Math.max(urlParams['page'], 0);
    }

    this.updateURLParams();
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
      let urlParams = {'page': this.page};
      axios.get('api/get_relmons', { params: urlParams }).then(response => {
        this.fetchedData = response.data.data;
        this.totalRows = response.data.total_rows;
        this.pageSize = response.data.page_size;
      });
    },
    fetchUserInfo() {
      let component = this;
      axios.get('api/user').then(response => {
        component.userInfo.name = response.data.fullname;
        component.userInfo.authorized = response.data.authorized_user;
      });
    },
    updateURLParams() {
      let urlParams = {'page': this.page};
      urlParams = new URLSearchParams(urlParams);
      window.history.replaceState('search', '', '?' + urlParams.toString());
    },
    previousPage() {
      this.page -= 1;
      this.updateURLParams();
      this.refetchRelmons();
    },
    nextPage() {
      this.page += 1;
      this.updateURLParams();
      this.refetchRelmons();
    },
  }
}
</script>

<style scoped>
</style>
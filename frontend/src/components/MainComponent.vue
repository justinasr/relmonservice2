<template>
  <v-app style="background-color: #fafafa">
    <v-container>
      <TopBarComponent @refetchRelmons="refetchRelmons" :userInfo="userInfo" ref="createNewRelMonComponent"></TopBarComponent>
      <RelMonComponent @editRelmon="editRelmon" @refetchRelmons="refetchRelmons" v-for="relmonData in fetchedData" :key="relmonData.name" :relmonData="relmonData" :userInfo="userInfo"></RelMonComponent>
      <v-row style="line-height: 36px; text-align: center;">
        <v-col class="elevation-3 pa-2 mb-2" style="background: white">
          <v-btn small color="primary" style="float: left" class="ma-1" v-if="page > 0" @click="previousPage()">Previous Page</v-btn>
          <span class="font-weight-light">Pages:</span>
          <span v-for="(p, i) in totalPages()" class="ml-1">
            <a v-if="i !== page" :href="'?page=' + i" style="text-decoration: none">{{i}}</a>
            <b v-if="i === page">{{i}}</b>
          </span>
          <v-btn small color="primary" style="float: right" class="ma-1" v-if="(page + 1) * pageSize < totalRows" @click="nextPage()">Next Page</v-btn>
        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script>
import axios from 'axios'
import RelMonComponent from './RelMonComponent';
import TopBarComponent from './TopBarComponent';

export default {
  name: 'MainComponent',
  data () {
    return {
      fetchedData: {},
      userInfo: {'name': '', 'authorized': false},
      page: 0,
      totalRows: 0,
      pageSize: 0,
      query: '',
    }
  },
  created () {
    let urlParams = Object.fromEntries(new URLSearchParams(window.location.search));
    if (!('page' in urlParams)) {
      this.page = 0;
    } else {
      this.page = Math.max(urlParams['page'], 0);
    }
    if (!('q' in urlParams)) {
      this.query = '';
    } else {
      this.query = urlParams['q'];
    }

    this.updateURLParams();
    this.refetchRelmons();
    this.fetchUserInfo();
  },
  watch: {
  },
  components: {
    RelMonComponent,
    TopBarComponent
  },
  methods: {
    editRelmon(relmon) {
      this.$refs.createNewRelMonComponent.startEditing(relmon)
    },
    refetchRelmons() {
      let urlParams = Object.fromEntries(new URLSearchParams(window.location.search));
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
      if (this.query.length > 0) {
        urlParams['q'] = this.query;
      }
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
    totalPages() {
      return Math.max(1, Math.ceil(this.totalRows / Math.max(1, this.pageSize)));
    }
  }
}
</script>

<style scoped>
</style>
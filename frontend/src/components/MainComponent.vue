<template>
  <v-app style="background-color: #fafafa">
    <v-container>
      <TopBarComponent @refetchRelmons="refetchRelmons" :userInfo="userInfo" ref="createNewRelMonComponent"></TopBarComponent>
      <div v-if="loading" class="ma-3" style="text-align: center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </div>
      <RelMonComponent @editRelmon="editRelmon" @refetchRelmons="refetchRelmons" v-for="relmonData in fetchedData" :key="relmonData.name" :relmonData="relmonData" :userInfo="userInfo"></RelMonComponent>
      <div style="line-height: 28px; text-align: center;">
        <div class="elevation-3 pl-4 pr-4 pt-2 pb-2" style="background: white">
          <v-row>
            <v-col :cols="12">
              <v-btn small color="primary" style="float: left" v-if="page > 0" @click="previousPage()">Previous Page</v-btn>
              <span class="font-weight-light">Pages:</span>
              <span v-for="(p, i) in totalPages()" class="ml-1">
                <a v-if="i !== page" :href="'?page=' + i" style="text-decoration: none">{{i}}</a>
                <b v-if="i === page">{{i}}</b>
              </span>
              <v-btn small color="primary" style="float: right" v-if="(page + 1) * pageSize < totalRows" @click="nextPage()">Next Page</v-btn>
            </v-col>
          </v-row>
        </div>
      </div>
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
      loading: false,
      page: 0,
      totalRows: 0,
      pageSize: 0,
      query: '',
    }
  },
  props: {
    userInfo: {
      type: Object,
      default: function () { return { 'name': '', 'authorized': false }; }
    }
  },
  created () {
    let urlParams = Object.fromEntries(new URLSearchParams(window.location.search));
    if (!('page' in urlParams)) {
      this.page = 0;
    } else {
      this.page = Math.max(parseInt(urlParams['page']), 0);
    }
    if (!('q' in urlParams)) {
      this.query = '';
    } else {
      this.query = urlParams['q'];
    }

    this.updateURLParams();
    this.refetchRelmons();
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
      if ('page' in urlParams) {
        this.page = parseInt(urlParams['page']);
      }
      if ('q' in urlParams) {
        this.query = urlParams['q'];
      }
      this.loading = true;
      this.fetchedData = {};
      axios.get('api/get_relmons', { params: urlParams }).then(response => {
        this.fetchedData = response.data.data;
        this.totalRows = response.data.total_rows;
        this.pageSize = response.data.page_size;
        this.loading = false;
      }).catch(error => {
        this.fetchedData = {};
        this.totalRows = 0;
        this.loading = false;
        alert('Error fetching relmons');
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

<template>
  <v-row>
    <v-col class="elevation-3 pa-4 mb-2" style="background: white; position: relative;">
      <span class="font-weight-light bigger-text">RelMon</span> <span class="ml-2 bigger-text">{{relmonData.name}}</span>
      <v-row>
        <v-col cols=5>
          Job information
          <ul>
            <li><span class="font-weight-light">ID:</span> {{relmonData.id}}</li>
            <li><span class="font-weight-light">Status:</span> {{relmonData.status}} <span v-if="relmonData.status == 'done'">
              | <a target="_blank" :href="'http://pdmv-new-relmon.web.cern.ch/pdmv-new-relmon#' + relmonData.name">open reports</a>
            </span></li>
            <li><span class="font-weight-light">HTCondor job status:</span> {{relmonData.condor_status}}</li>
            <li><span class="font-weight-light">HTCondor job ID:</span> {{relmonData.condor_id}}</li>
            <li><span class="font-weight-light">Last update:</span> {{relmonData.last_update}}</li>
          </ul>
          Progress
          <ul>
            <li><span class="font-weight-light">Download:</span>
              <v-progress-linear :value="relmonData.downloaded_relvals / relmonData.total_relvals * 100"
                                 color="success"
                                 height="16"
                                 class="elevation-1"
                                 style="max-width: 250px; color: white; border-radius: 4px">
                <small><strong>{{ Math.ceil(relmonData.downloaded_relvals / relmonData.total_relvals * 100) }}%</strong></small>
              </v-progress-linear>
            </li>
            <li><span class="font-weight-light">Comparison:</span>
              <v-progress-linear :value="relmonData.done_size / relmonData.total_size * 100"
                                 color="primary"
                                 height="16"
                                 class="elevation-1"
                                 style="max-width: 250px; color: white; border-radius: 4px">
                <small><strong>{{ Math.ceil(relmonData.done_size / relmonData.total_size * 100) }}%</strong></small>
              </v-progress-linear>
            </li>
          </ul>
          Actions
          <br>
          <v-btn small class="ma-1" color="primary" @click="editRelmon(relmonData)">Edit</v-btn>
          <v-btn small class="ma-1" color="error" @click="resetOverlay = true">Reset</v-btn>
          <v-btn small class="ma-1" color="error" @click="deleteOverlay = true">Delete</v-btn>
        </v-col>
        <v-col cols=7>
          Categories
          <ul>
            <li v-for="category in relmonData.categories"><span class="font-weight-light">{{category.name}}</span> - {{category.status}} <span class="font-weight-light">| HLT:</span> {{category.hlt}} <span class="font-weight-light">| pairing:</span> {{category.automatic_pairing ? 'auto' : 'manual'}}
              <ul>
                <li>
                  <span class="font-weight-light">References</span>
                  <span class="font-weight-light"> - total:</span> {{category.reference.length}}
                  <!-- <span class="font-weight-light"> | size:</span>&nbsp;{{Math.round((category.reference_total_size / 1024.0 / 1024.0) * 10) / 10}}MB -->
                  <span v-for="value, key in category.reference_status"><span class="font-weight-light"> | {{key}}:&nbsp;</span>{{value}}</span>
                </li>
                <li>
                  <span class="font-weight-light">Targets</span>
                  <span class="font-weight-light"> - total:</span> {{category.target.length}}
                  <!-- <span class="font-weight-light"> | size:</span>&nbsp;{{Math.round((category.target_total_size / 1024.0 / 1024.0) * 10) / 10}}MB -->
                  <span v-for="value, key in category.target_status"><span class="font-weight-light"> | {{key}}:&nbsp;</span>{{value}}</span>
                </li>
              </ul>
            </li>
          </ul>
        </v-col>

        <v-overlay :absolute="false"
                   :opacity="0.95"
                   :z-index="3"
                   :value="resetOverlay"
                   style="text-align: center">
          Reset {{relmonData.name}}?<br>
          <v-btn color="error"
                 class="ma-1"
                 small
                 v-if="!isRefreshing"
                 @click="resetRelmon(relmonData)">
            Reset
          </v-btn>
          <v-btn color="primary"
                 class="ma-1"
                 small
                 v-if="!isRefreshing"
                 @click="resetOverlay = false">
            Cancel
          </v-btn>
          <v-progress-circular indeterminate
                               v-if="isRefreshing"
                               color="primary"></v-progress-circular>
        </v-overlay>

        <v-overlay :absolute="false"
                   :opacity="0.95"
                   :z-index="3"
                   :value="deleteOverlay"
                   style="text-align: center">
          Delete {{relmonData.name}}?<br>
          <v-btn color="error"
                 class="ma-1"
                 small
                 v-if="!isRefreshing"
                 @click="deleteRelmon(relmonData)">
            Delete
          </v-btn>
          <v-btn color="primary"
                 class="ma-1"
                 small
                 v-if="!isRefreshing"
                 @click="deleteOverlay = false">
            Cancel
          </v-btn>
          <v-progress-circular indeterminate
                               v-if="isRefreshing"
                               color="primary"></v-progress-circular>
        </v-overlay>
      </v-row>
    </v-col>
  </v-row>
</template>

<script>
import axios from 'axios'
export default {
  name: 'RelMonComponent',
  data () {
    return {
      resetOverlay: false,
      deleteOverlay: false,
      isRefreshing: false
    }
  },
  created () {

  },
  watch: {
  },
  props: {
    relmonData: {
      type: Object,
      default: () => {}
    }
  },
  components: {
  },
  methods: {
    editRelmon(relmon) {
      this.$emit('editRelmon', relmon)
    },
    resetRelmon(relmon) {
      let component = this;
      component.isRefreshing = true;
      axios.post('relmonsvc/api/reset', {
        'id': component.relmonData.id
      }).then(response => {
        setTimeout(function(){
          component.refetchRelmons();
          component.resetOverlay = false;
          component.isRefreshing = false;
        }, 5000);
      });
    },
    deleteRelmon(relmon) {
      let component = this;
      component.isRefreshing = true;
      axios.delete('relmonsvc/api/delete', { data:{
        'id': component.relmonData.id
      }
      }).then(response => {
        setTimeout(function(){
          component.refetchRelmons();
          component.deleteOverlay = false;
          component.isRefreshing = false;
        }, 5000);
      });
    },
    refetchRelmons() {
      this.$emit('refetchRelmons')
    }
  }
}
</script>

<style scoped>
.bigger-text {
  font-size: 1.5rem;
}

li {
  padding-bottom: 4px;
}
</style>
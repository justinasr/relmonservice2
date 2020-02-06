<template>
  <v-row>
    <v-col class="elevation-3 pa-4 mb-2" style="background: white; position: relative;">
      <span class="font-weight-light bigger-text">RelMon</span> <span class="ml-2 bigger-text">{{relmonData.name}}</span>
      <v-row>
        <v-col :lg="5" :md="6" :sm="6" :cols="12">
          Job information
          <ul>
            <li><span class="font-weight-light">ID:</span> {{relmonData.id}}</li>
            <li><span class="font-weight-light">Status:</span> {{relmonData.status}} <span v-if="relmonData.status == 'done'">
              | <a target="_blank" :href="'http://pdmv-new-relmon.web.cern.ch/pdmv-new-relmon#' + relmonData.name">go to reports</a>
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
          <div v-if="userInfo.authorized">
            Actions
            <br>
            <v-btn small class="ma-1" color="primary" @click="editRelmon(relmonData)">Edit</v-btn>
            <v-btn small class="ma-1" color="error" @click="resetOverlay = true">Reset</v-btn>
            <v-btn small class="ma-1" color="error" @click="deleteOverlay = true">Delete</v-btn>
          </div>
        </v-col>
        <v-col :lg="7" :md="6" :sm="6" :cols="12">
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
          <v-btn small class="ma-1" color="primary" @click="detailedView = true">Open detailed view</v-btn>
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
    <v-dialog v-model="detailedView">
      <v-card class="pa-4" >
        <span class="font-weight-light bigger-text">Categories of</span> <span class="ml-2 bigger-text">{{relmonData.name}}</span>
        <div v-for="category in relmonData.categories">
          <span class="font-weight-light bigger-text">{{category.name}}</span>
          <ul>
            <li><span class="font-weight-light">Status:</span> {{category.status}}</li>
            <li><span class="font-weight-light">HLT:</span> {{category.hlt}}</li>
            <li><span class="font-weight-light">Pairing:</span> {{category.automatic_pairing ? 'auto' : 'manual'}}</li>
            <li>
              <span class="font-weight-light">References</span>
              <span class="font-weight-light"> - total:</span> {{category.reference.length}}
              <span class="font-weight-light"> | size:</span>&nbsp;{{Math.round((category.reference_total_size / 1024.0 / 1024.0) * 10) / 10}}MB
              <span v-for="value, key in category.reference_status"><span class="font-weight-light"> | {{key}}:&nbsp;</span>{{value}}</span>
              <ul>
                <li v-for="reference in category.reference">
                  <span class="font-weight-light">Name:</span> {{reference.name}} | <span class="font-weight-light">Status:</span> <span :class="reference.status | statusToColor">{{reference.status}}</span> <span class="font-weight-light"> | Size:</span> {{Math.round((reference.file_size / 1024.0 / 1024.0) * 10) / 10}}MB
                </li>
              </ul>
            </li>
            <li>
              <span class="font-weight-light">Targets</span>
              <span class="font-weight-light"> - total:</span> {{category.target.length}}
              <span class="font-weight-light"> | size:</span>&nbsp;{{Math.round((category.target_total_size / 1024.0 / 1024.0) * 10) / 10}}MB
              <span v-for="value, key in category.target_status"><span class="font-weight-light"> | {{key}}:&nbsp;</span>{{value}}</span>
              <ul>
                <li v-for="target in category.target">
                  <span class="font-weight-light">Name:</span> {{target.name}} | <span class="font-weight-light">Status:</span> <span :class="target.status | statusToColor">{{target.status}}</span> <span class="font-weight-light"> | Size:</span> {{Math.round((target.file_size / 1024.0 / 1024.0) * 10) / 10}}MB
                </li>
              </ul>
            </li>
          </ul>
        </div>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="ma-1" color="primary" @click="detailedView = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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
      isRefreshing: false,
      detailedView: false
    }
  },
  created () {

  },
  watch: {
  },
  filters: {
    statusToColor (status) {
      if (status.startsWith("no_")) {
        return "red-text";
      }
      return "";
    }
  },
  props: {
    relmonData: {
      type: Object,
      default: () => {}
    },
    userInfo: {
      type: Object,
      default: function () { return { 'name': '', 'authorized': false }; }
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
      axios.post('api/reset', {
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
      axios.delete('api/delete', { data:{
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
  word-break: break-all;
}

li {
  padding-bottom: 4px;
}

.red-text {
  color: red;
}
</style>
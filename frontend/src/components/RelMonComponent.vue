<template>
  <v-row>
    <v-col class="elevation-3 pa-2 mb-2" style="background: white; position: relative;">
      <span class="font-weight-light">RelMon</span> {{relmonData.name}}
      <v-row>
        <v-col>
          Job information
          <ul>
            <li><small>ID:</small> {{relmonData.id}}</li>
            <li><small>Status:</small> {{relmonData.status}}</li>
            <li><small>HTCondor job status:</small> {{relmonData.condor_status}}</li>
            <li><small>HTCondor job ID:</small> {{relmonData.condor_id}}</li>
            <li><small>Last update:</small> {{relmonData.last_update}}</li>
          </ul>
          <v-btn small class="ma-1" color="primary" @click="editRelmon(relmonData)">Edit</v-btn>
          <v-btn small class="ma-1" color="error" @click="resetOverlay = true">Reset</v-btn>
          <v-btn small class="ma-1" color="error" @click="deleteOverlay = true">Delete</v-btn>
        </v-col>
        <v-col>
          Categories
          <ul>
            <li v-for="category in relmonData.categories">{{category.name}} <small>(HLT: {{category.hlt}}, pairing: {{category.automatic_pairing ? 'auto' : 'manual'}})</small>
              <ul>
                <li>References <small>({{category.reference.length}} | {{Math.round((category.reference_total_size / 1024.0 / 1024.0) * 10) / 10}}MB)</small>
                  <ul>
                    <li v-for="value, key in category.reference_status">{{key}}: {{value}}</li>
                  </ul>
                </li>
                <li>Targets <small>({{category.target.length}} | {{Math.round((category.target_total_size / 1024.0 / 1024.0) * 10) / 10}}MB)</small>
                  <ul>
                    <li v-for="value, key in category.target_status">{{key}}: {{value}}</li>
                  </ul>
                </li>
              </ul>
            </li>
          </ul>
        </v-col>

        <v-overlay :absolute="true"
                   :opacity="0.95"
                   :z-index="3"
                   :value="resetOverlay"
                   style="text-align: center">
          Reset {{relmonData.name}}?<br>
          <v-btn color="error"
                 class="ma-1"
                 @click="resetRelmon(relmonData)">
            Reset
          </v-btn>
          <v-btn color="primary"
                 class="ma-1"
                 @click="resetOverlay = false">
            Cancel
          </v-btn>
        </v-overlay>

        <v-overlay :absolute="true"
                   :opacity="0.95"
                   :z-index="3"
                   :value="deleteOverlay"
                   style="text-align: center">
          Delete {{relmonData.name}}?<br>
          <v-btn color="error"
                 class="ma-1"
                 @click="deleteRelmon(relmonData)">
            Delete
          </v-btn>
          <v-btn color="primary"
                 class="ma-1"
                 @click="deleteOverlay = false">
            Cancel
          </v-btn>
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
      let component = this
      axios.post('/relmonsvc/api/reset', {
        'id': component.relmonData.id
      }).then(response => {
        console.log(response.data);
        component.resetOverlay = false;
      });
    },
    deleteRelmon(relmon) {
      let component = this
      axios.delete('/relmonsvc/api/delete', {data:{
        'id': component.relmonData.id
      }
      }).then(response => {
        console.log(response.data);
        component.deleteOverlay = false;
      });
    }
  }
}
</script>

<style scoped>
</style>
<template>
  <v-row>
    <v-col class="elevation-3 pa-2 mb-2" style="background: white">
      <!-- <pre>{{relmonWrapper.relmon}}</pre> -->
      <v-btn small color="primary" v-if="!overlay.length" class="ma-1" @click="overlay = overlay.length ? [] : [0]">
        Create New RelMon
      </v-btn>
      <v-btn small color="primary" v-if="!overlay.length" class="ma-1" @click="forceRefresh()">
        Force Refresh
      </v-btn>
      <v-expansion-panels multiple v-model="overlay">
        <v-expansion-panel :key="0" class="elevation-0">
          <v-expansion-panel-content>
            <v-row>
              <v-col v-if="!isEditing" cols=12>
                <h3>Creating new RelMon</h3>
              </v-col>
              <v-col v-if="isEditing" cols=12>
                <h3>Editing "{{relmonWrapper.relmon.name}}"</h3>
              </v-col>
              <v-col cols=12 sm=12 md=8 lg=8>
                <span>Name:</span><input type="text" :disabled="isEditing" style="width: 100%" v-model="relmonWrapper.relmon.name">
              </v-col>
              <v-col v-if="isEditing" cols=12 sm=12 md=4 lg=4>
                <span>ID:</span><input type="text" :disabled="true" style="width: 100%" v-model="relmonWrapper.relmon.id">
              </v-col>
            </v-row>
            <v-row>
              <v-col cols=12>
                <v-tabs :grow="true" :centered="true">
                  <v-tabs-slider></v-tabs-slider>
                  <v-tab v-for="category in relmonWrapper.relmon.categories" :key="category.name" :href="`#tab-${category.name}`">
                    {{ category.name }}
                  </v-tab>
                  <v-tab-item v-for="category in relmonWrapper.relmon.categories" :key="category.name" :value="'tab-' + category.name">
                    <v-row>
                      <v-col cols=12>
                        {{category.name}} references:<br>
                        <textarea v-model="category.reference"></textarea>
                        {{category.name}} targets:<br>
                        <textarea v-model="category.target"></textarea>
                      </v-col>
                      <v-col cols=6>
                        Pairing:
                        <v-btn-toggle mandatory v-model="category.automatic_pairing">
                          <v-btn small :value="true">
                            Automatic
                          </v-btn>
                          <v-btn small :value="false">
                            Manual
                          </v-btn>
                        </v-btn-toggle>
                      </v-col>
                      <v-col cols=6>
                        HLT:
                        <v-btn-toggle mandatory v-model="category.hlt">
                          <v-btn small :value="'no'" :disabled="category.name === 'Generator'">
                            No HLT
                          </v-btn>
                          <v-btn small :value="'only'">
                            Only HLT
                          </v-btn>
                          <v-btn small :value="'both'" :disabled="category.name === 'Generator'">
                            Both
                          </v-btn>
                        </v-btn-toggle>
                      </v-col>
                    </v-row>
                  </v-tab-item>
                </v-tabs>
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-btn v-if="!isEditing" small class="ma-1" color="primary" @click="createRelmon()">Create</v-btn>
                <v-btn v-if="isEditing" small class="ma-1" color="primary" @click="editOverlay = true">Save</v-btn>
                <v-btn small class="ma-1" color="error" @click="cancelCreation()">Cancel</v-btn>
              </v-col>
            </v-row>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-col>

    <v-overlay :absolute="false"
               :opacity="0.95"
               :z-index="3"
               :value="editOverlay"
               style="text-align: center">
      This will reset {{relmonWrapper.relmon.name}}. All progress will be lost. Are you sure you want to update {{relmonWrapper.relmon.name}}?<br>
      <v-btn color="error"
             class="ma-1"
             @click="editRelmon()">
        Yes
      </v-btn>
      <v-btn color="primary"
             class="ma-1"
             @click="editOverlay = false">
        No
      </v-btn>
    </v-overlay>

  </v-row>
</template>

<script>
import axios from 'axios'
export default {
  name: 'CreateNewRelMonComponent',
  data () {
    return {
      categories: ['Data', 'FullSim', 'FastSim', 'Generator', 'FullSim PU', 'FastSim PU'],
      overlay: [],
      relmonWrapper: {'relmon': {}},
      isEditing: false,
      editOverlay: false,
      name: ''
    }
  },
  created () {
    this.relmonWrapper['relmon'] = this.createEmptyRelmon();
  },
  watch: {

  },
  props: {

  },
  components: {
  },
  methods: {
    createRelmon() {
      var relmonClone = JSON.parse(JSON.stringify(this.relmonWrapper.relmon))
      relmonClone.categories.forEach(function(item, index) {
        item['name'] = item['name'].replace(' ', '_')
        item['reference'] = item['reference'].split('\n').filter(Boolean)
        item['target'] = item['target'].split('\n').filter(Boolean)
      })
      axios.post('/relmonsvc/api/create', relmonClone).then(response => {
        console.log(response.data);
        this.isEditing = false
        this.relmonWrapper['relmon'] = this.createEmptyRelmon();
        this.overlay = [];
      });
    },
    editRelmon() {
      var relmonClone = JSON.parse(JSON.stringify(this.relmonWrapper.relmon))
      relmonClone.categories.forEach(function(item, index) {
        item['name'] = item['name'].replace(' ', '_')
        item['reference'] = item['reference'].split('\n').filter(Boolean)
        item['target'] = item['target'].split('\n').filter(Boolean)
      })
      axios.post('/relmonsvc/api/edit', relmonClone).then(response => {
        console.log(response.data);
        this.isEditing = false
        this.relmonWrapper['relmon'] = this.createEmptyRelmon();
        this.overlay = [];
        this.editOverlay = false;
      });
    },
    cancelCreation() {
      this.isEditing = false
      this.relmonWrapper['relmon'] = this.createEmptyRelmon();
      this.overlay = [];
    },
    startEditing(relmon) {
      if (relmon) {
        var relmonClone = JSON.parse(JSON.stringify(relmon))
        relmonClone.categories.forEach(function(item, index) {
          item['name'] = item['name'].replace('_', ' ')
          item['reference'] = item['reference'].map(x => x['name']).filter(Boolean).join('\n')
          item['target'] = item['target'].map(x => x['name']).filter(Boolean).join('\n')
        })
        this.isEditing = true;
        this.relmonWrapper.relmon = this.addMissingCategories(relmonClone);
        this.overlay = [0];
        window.scrollTo(0,0);
      } else {
        this.isEditing = false
        this.relmonWrapper['relmon'] = this.createEmptyRelmon();
        this.overlay = [];
      }
    },
    createEmptyRelmon() {
      var relmon = {'name': '',
                    'categories': []}
      relmon = this.addMissingCategories(relmon)
      return relmon;
    },
    addMissingCategories(relmon) {
      let relmonCategories = relmon['categories'].map(x => x['name'])
      this.categories.forEach(function(item, index) {
        if (!relmonCategories.includes(item)) {
          relmon['categories'].push({'name': item,
                                     'hlt': item === 'Generator' ? 'only' : 'both',
                                     'automatic_pairing': true,
                                     'reference':'',
                                     'target': ''})
        }
      })
      let component = this
      relmon['categories'] = relmon['categories'].sort(function(a, b) {return component.categories.indexOf(a['name']) - component.categories.indexOf(b['name'])})
      return relmon
    },
    forceRefresh() {
      axios.get('/relmonsvc/api/tick').then(response => {
        alert(response.data.message)
      });
    }
  }
}
</script>

<style scoped>
textarea{
  width: 100%;
  border-style: solid;
  min-height: 250px;
}
input {
  border-style: solid;
  border-width: 1px;
  border-color: rgb(169, 169, 169);
}
.font-weight-500 {
  font-weight: 500;
}
.v-tab--active {
  background-color: rgba(0,0,0,0.05);
}
.elevation-0::before {
  box-shadow: none !important;
  -webkit-box-shadow: none !important;
}
</style>
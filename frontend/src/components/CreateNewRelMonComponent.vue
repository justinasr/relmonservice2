<template>
  <v-row>
    <v-col class="elevation-3 pa-2 mb-2" style="background: white">
      <!-- <pre>{{relmonWrapper.relmon}}</pre> -->
      <v-btn small color="primary" v-if="!expandedPanels.length && userInfo.authorized" class="ma-1" @click="expandedPanels = expandedPanels.length ? [] : [0]" title="Create a new RelMon">
        Create New RelMon
      </v-btn>
      <v-btn small color="primary" v-if="!expandedPanels.length && userInfo.authorized" class="ma-1" @click="forceRefresh()" title="Trigger RelMon Service to check RelMon progress in HTCondor. This happens automatically every 10 minutes">
        Trigger a Refresh
      </v-btn>
      <div style="float: right; line-height: 36px;">
        <span class="font-weight-light">Logged in as</span> {{userInfo.name}}
        <span v-if="userInfo.authorized">&#11088;</span>
      </div>
      <v-expansion-panels multiple v-model="expandedPanels">
        <v-expansion-panel :key="0" class="elevation-0">
          <v-expansion-panel-content>
            <v-row>
              <v-col v-if="!isEditing" cols=12>
                <span class="bigger-text font-weight-light">Creating</span> <span class="bigger-text ml-2">a new RelMon</span>
              </v-col>
              <v-col v-if="isEditing" cols=12>
                <span class="bigger-text font-weight-light">Editing</span> <span class="bigger-text ml-2">{{relmonWrapper.relmon.name}}</span>
              </v-col>
              <v-col cols=12 sm=12 md=8 lg=8>
                <span class="font-weight-light">Name:</span><input type="text" style="width: 100%" v-model="relmonWrapper.relmon.name">
              </v-col>
              <v-col v-if="isEditing" cols=12 sm=12 md=4 lg=4>
                <span class="font-weight-light">ID:</span><input type="text" :disabled="true" style="width: 100%" v-model="relmonWrapper.relmon.id">
              </v-col>
            </v-row>
            <v-row>
              <v-col cols=12>
                <v-tabs :grow="true" :centered="true">
                  <v-tabs-slider></v-tabs-slider>
                  <v-tab v-for="category in relmonWrapper.relmon.categories" :key="category.name" :href="`#tab-${category.name}`">
                    <div>
                      <div>
                        {{ category.name }}
                      </div>
                      <small>
                        {{listLength(category.reference)}} vs. {{listLength(category.target)}}
                      </small>
                    </div>
                  </v-tab>
                  <v-tab-item v-for="category in relmonWrapper.relmon.categories" :key="category.name" :value="'tab-' + category.name">
                    <v-row>
                      <v-col cols=12>
                        <span class="font-weight-light">{{category.name}} references:</span><br>
                        <textarea v-model="category.reference"></textarea>
                        <span class="font-weight-light">{{category.name}} targets:</span><br>
                        <textarea v-model="category.target"></textarea>
                      </v-col>
                      <v-col cols=6>
                        <span class="font-weight-light">Pairing:</span>
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
                        <span class="font-weight-light">HLT:</span>
                        <v-btn-toggle mandatory v-model="category.hlt">
                          <v-btn small :value="'no'">
                            No HLT
                          </v-btn>
                          <v-btn small :value="'only'" :disabled="category.name === 'Generator'">
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
                <v-btn v-if="!isEditing" small class="ma-1" color="primary" :disabled="!relmonWrapper.relmon.name" @click="updateRelmon('create')">Create</v-btn>
                <v-btn v-if="isEditing" small class="ma-1" color="primary" :disabled="!relmonWrapper.relmon.name" @click="editOverlay = true">Save</v-btn>
                <v-btn small class="ma-1" color="error" @click="cleanup()">Cancel</v-btn>
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
      <span v-if="relmonWrapper.relmon.status == 'done'">This will update {{relmonWrapper.relmon.name}}. All progress of changed categories will be lost and these categories will be redone from scratch.</span>
      <span v-if="relmonWrapper.relmon.status != 'done'">This will update and reset {{relmonWrapper.relmon.name}}. All progress will be lost and RelMon will be redone from scratch.</span>
      <br>Are you sure you want to update {{relmonWrapper.relmon.name}}?<br>
      <v-btn color="error"
             class="ma-1"
             small
             v-if="!isRefreshing"
             @click="updateRelmon('edit')">
        Yes
      </v-btn>
      <v-btn color="primary"
             class="ma-1"
             small
             v-if="!isRefreshing"
             @click="editOverlay = false">
        No
      </v-btn>
      <v-progress-circular indeterminate
                           v-if="isRefreshing"
                           color="primary"></v-progress-circular>
    </v-overlay>

    <v-overlay :absolute="false"
               :opacity="0.95"
               :z-index="3"
               :value="creatingOverlay"
               style="text-align: center">
      Creating {{relmonWrapper.relmon.name}}<br>
      <v-progress-circular indeterminate
                     color="primary"></v-progress-circular>
    </v-overlay>

    <v-overlay :absolute="false"
               :opacity="0.95"
               :z-index="3"
               :value="forceRefreshOverlay"
               style="text-align: center">
      Refresh has been triggered. RelMon Service will now check how submitted RelMons are progressing in HTCondor. This may take a few minutes. This refresh happens automatically on it's own every 10 minutes.<br>
      <v-btn color="primary"
             class="ma-1"
             small
             @click="forceRefreshOverlay = false; refetchRelmons();">
        Close
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
      expandedPanels: [],
      relmonWrapper: {'relmon': {}},
      isEditing: false,
      editOverlay: false,
      creatingOverlay: false,
      isRefreshing: false,
      forceRefreshOverlay: false,
    }
  },
  created () {
    this.cleanup();
  },
  watch: {

  },
  props: {
    userInfo: {
      type: Object,
      default: function () { return { 'name': '', 'authorized': false }; }
    }
  },
  components: {
  },
  methods: {
    updateRelmon(action) {
      var relmonClone = JSON.parse(JSON.stringify(this.relmonWrapper.relmon))
      let component = this;
      this.isRefreshing = true;
      if (action === 'create') {
        this.creatingOverlay = true;
      }
      relmonClone.categories.forEach(function(item, index) {
        item['name'] = item['name'].replace(' ', '_')
        item['reference'] = item['reference'].split('\n').filter(Boolean)
        item['target'] = item['target'].split('\n').filter(Boolean)
      })
      axios.post('api/' + action, relmonClone).then(response => {
        setTimeout(function(){
          component.refetchRelmons();
          component.cleanup();
          component.isRefreshing = false;
        }, action === 'create' ? 5000 : 500);
      });
    },
    cleanup() {
      this.isEditing = false
      this.editOverlay = false;
      this.creatingOverlay = false;
      this.relmonWrapper['relmon'] = this.createEmptyRelmon();
      this.expandedPanels = [];
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
        relmonClone['categories'] = this.addMissingCategories(relmonClone.categories);
        this.expandedPanels = [0];
        window.scrollTo(0,0);
        this.relmonWrapper.relmon = relmonClone;
      } else {
        this.cleanup()
      }
    },
    listLength(l) {
      return l.split('\n').filter(Boolean).length;
    },
    createEmptyRelmon() {
      return {'name': '',
              'categories': this.addMissingCategories([])}
    },
    addMissingCategories(categories) {
      let existingCategoryNames = categories.map(x => x['name'])
      this.categories.forEach(function(item, index) {
        if (!existingCategoryNames.includes(item)) {
          categories.push({'name': item,
                           'hlt': item === 'Generator' ? 'only' : 'both',
                           'automatic_pairing': true,
                           'reference':'',
                           'target': ''})
        }
      })
      let component = this
      categories = categories.sort(function(a, b) {return component.categories.indexOf(a['name']) - component.categories.indexOf(b['name'])})
      return categories
    },
    forceRefresh() {
      let component = this;
      axios.get('api/tick').then(response => {
        component.forceRefreshOverlay = true;
      });
    },
    refetchRelmons() {
      this.$emit('refetchRelmons')
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
.v-tab--active {
  background-color: rgba(0,0,0,0.05);
}
.elevation-0::before {
  box-shadow: none !important;
  -webkit-box-shadow: none !important;
}
.bigger-text {
  font-size: 1.5rem;
}
</style>
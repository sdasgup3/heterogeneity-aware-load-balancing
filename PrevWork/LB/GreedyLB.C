/**
 * \addtogroup CkLdb
*/
/*@{*/

/*
 status:
  * support processor avail bitvector
  * support nonmigratable attrib
      nonmigratable object load is added to its processor's background load
      and the nonmigratable object is not taken in the objData array
*/

#include <algorithm>

#include "charm++.h"


#include "ckgraph.h"
#include "cklists.h"
#include "GreedyLB.h"
#include <assert.h>


using namespace std;

CreateLBFunc_Def(GreedyLB, "always assign the heaviest obj onto lightest loaded processor.")

GreedyLB::GreedyLB(const CkLBOptions &opt): CentralLB(opt)
{
  lbname = "GreedyLB";
  if (CkMyPe()==0)
    CkPrintf("[%d] GreedyLB created\n",CkMyPe());
}

bool GreedyLB::QueryBalanceNow(int _step)
{
  //  CkPrintf("[%d] Balancing on step %d\n",CkMyPe(),_step);
  return true;
}

class ProcLoadGreater {
  public:
    bool operator()(ProcInfo p1, ProcInfo p2) {
      return (p1.totalLoad() > p2.totalLoad());
    }
};

class ObjLoadGreater {
  public:
    bool operator()(Vertex v1, Vertex v2) {
      return (v1.getVertexLoad() > v2.getVertexLoad());
    }
};

void GreedyLB::work(LDStats* stats)
{
  int  obj, objCount, pe;
  int n_pes = stats->nprocs();
  int n_objs  = stats->n_objs;
  int *map = new int[n_pes];
  double* objTime  = new double[n_pes];
  double* bgTime  = new double[n_pes];
  double* idleTime  = new double[n_pes];
  double* wall_times  = new double[n_pes];

  /************* CS 533 *********************/
  int * init_dist =  new int[n_pes];
  int * final_dist =  new int[n_pes];

  for(pe = 0; pe < n_pes; pe++) {
    init_dist[pe] = 0 ;
    final_dist[pe] = 0 ;
  }
  /************* CS 533 *********************/

  /*
  double *F = new double[n_pes];
  for(int pe = 0; pe < n_pes; pe++) {
    F[pe] = 1;
  }
  for (int obj = 0; obj < stats->n_objs; obj++)
  {
      LDObjData &oData = stats->objData[obj];
      F[stats->from_proc[obj]] += oData.wallTime;
  }


  for(int pe = 0; pe < n_pes; pe++) {
    struct ProcStats &proc = stats->procs[pe];
    proc.pe_speed =  1/ F[pe];
  }
  */

  std::vector<ProcInfo>  procs;
  for(pe = 0; pe < n_pes; pe++) {
    map[pe] = -1;
    if (stats->procs[pe].available) {
      map[pe] = procs.size();
      procs.push_back(ProcInfo(pe, stats->procs[pe].bg_walltime, 0.0, stats->procs[pe].pe_speed, true));
    }
  }

  // take non migratbale object load as background load
  for (obj = 0; obj < stats->n_objs; obj++)
  {
      LDObjData &oData = stats->objData[obj];
      if (!oData.migratable)  {
        int pe = stats->from_proc[obj];
        pe = map[pe];
        if (pe==-1)
          CmiAbort("GreedyLB: nonmigratable object on an unavail processor!\n");
        procs[pe].totalLoad() += oData.wallTime;
      }
  }
  delete [] map;

  // considering cpu speed
  for (pe = 0; pe<procs.size(); pe++) {
    procs[pe].totalLoad() +=  procs[pe].overhead();
    procs[pe].totalLoad() *= procs[pe].pe_speed();
  }

  // build object array
  std::vector<Vertex> objs;

  for(int obj = 0; obj < stats->n_objs; obj++) {
    LDObjData &oData = stats->objData[obj];
    int pe = stats->from_proc[obj];
    if (!oData.migratable) {
      if (!stats->procs[pe].available) 
        CmiAbort("GreedyLB cannot handle nonmigratable object on an unavial processor!\n");
      continue;
    }
    double load = oData.wallTime * stats->procs[pe].pe_speed;
    objs.push_back(Vertex(obj, load, stats->objData[obj].migratable, stats->from_proc[obj]));
  }

  // max heap of objects
  sort(objs.begin(), objs.end(), ObjLoadGreater());
  // min heap of processors
  make_heap(procs.begin(), procs.end(), ProcLoadGreater());

  if (_lb_args.debug()>1) 
    CkPrintf("[%d] In GreedyLB strategy\n",CkMyPe());


    // greedy algorithm
  int nmoves = 0;
  for (obj=0; obj < objs.size(); obj++) {
    ProcInfo p = procs.front();
    pop_heap(procs.begin(), procs.end(), ProcLoadGreater());
    procs.pop_back();

    // Increment the time of the least loaded processor by the cpuTime of
    // the `heaviest' object
    p.totalLoad() += objs[obj].getVertexLoad();

    //Insert object into migration queue if necessary
    const int dest = p.getProcId();
    const int pe   = objs[obj].getCurrentPe();
    const int id   = objs[obj].getVertexId();
    if (dest != pe) {
      stats->to_proc[id] = dest;
      nmoves ++;
      if (_lb_args.debug()>2) 
        CkPrintf("[%d] Obj %d migrating from %d to %d\n", CkMyPe(),objs[obj].getVertexId(),pe,dest);
    }

    //Insert the least loaded processor with load updated back into the heap
    procs.push_back(p);
    push_heap(procs.begin(), procs.end(), ProcLoadGreater());
  }

  /***************CS 533**************************/
  for(int obj=0; obj < n_objs; obj++) {
    init_dist[stats->from_proc[obj]] ++;
    final_dist[stats->to_proc[obj]] ++;
  }
  for(int i=0;i< n_pes;i++){
    objTime[i]    = 0.0;
  }
  for(int obj = 0 ; obj<n_objs;obj++)  {
    objTime[stats->from_proc[obj]] +=  stats->objData[obj].wallTime;
  }
  for(int i=0;i< n_pes;i++){
    bgTime[i]     = (stats->procs[i]).bg_walltime;
    idleTime[i]   = (stats->procs[i]).idletime;
    wall_times[i] = (stats->procs[i]).total_walltime; 
  }
  for(int pe = 0; pe < n_pes; pe++) {
    printf("procid %d (w:%lf bg:%lf obj:%lf i:%lf) :%d->%d\n",
        pe, wall_times[pe],bgTime[pe],objTime[pe],idleTime[pe],init_dist[pe],final_dist[pe]);
  }
  /*****************************************/
    

  if (_lb_args.debug()>0) 
    CkPrintf("[%d] %d objects migrating.\n", CkMyPe(), nmoves);

  if (_lb_args.debug()>1)  {
    CkPrintf("CharmLB> Min obj: %f  Max obj: %f\n", objs[objs.size()-1].getVertexLoad(), objs[0].getVertexLoad());
    CkPrintf("CharmLB> PE speed:\n");
    for (pe = 0; pe<procs.size(); pe++)
      CkPrintf("%f ", procs[pe].pe_speed());
    CkPrintf("\n");
    CkPrintf("CharmLB> PE Load:\n");
    for (pe = 0; pe<procs.size(); pe++)
      CkPrintf("%f (%f)  ", procs[pe].totalLoad(), procs[pe].overhead());
    CkPrintf("\n");
  }

  if (_lb_args.metaLbOn()) {
    double max_load = 0;
    double avg_load = 0;
    for (pe = 0; pe<procs.size(); pe++) {
      if (procs[pe].totalLoad() > max_load) {
        max_load = procs[pe].totalLoad();
      }
      avg_load += procs[pe].totalLoad();
    }

    stats->after_lb_max = max_load;
    stats->after_lb_avg = avg_load/procs.size();
    stats->is_prev_lb_refine = 0;
    if (_lb_args.debug() > 0)
      CkPrintf("GreedyLB> After lb max load: %lf avg load: %lf\n", max_load, avg_load/procs.size());
  }
}

#include "GreedyLB.def.h"

/*@}*/





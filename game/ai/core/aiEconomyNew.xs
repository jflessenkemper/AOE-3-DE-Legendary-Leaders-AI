//==============================================================================
// livestockMonitor
// Build a Livestock Pen if we don't have one, then maintain sheep!
//==============================================================================
rule livestockMonitor
inactive
minInterval 30
{
   int sheepLimit = kbGetBuildLimit(cMyID, cUnitTypeSheep);
   int cowLimit = kbGetBuildLimit(cMyID, cUnitTypeCow);
   int llamaLimit = kbGetBuildLimit(cMyID, cUnitTypeLlama);
   
   int herdablePriority = 55;
   if (kbGetAge() < cAge3)
   {
      herdablePriority = 30;
   }
   
   static int sheepMaintain = -1;
   static int cowMaintain = -1;
   static int llamaMaintain = -1;
   
   // Livestock Pen for Europeans, Village for Chinese, Shrine for Japanese, and Sacred Field for Indians...
   if (civIsNative() == false)
   {
      if (kbUnitCount(cMyID, gLivestockPenUnit, cUnitStateABQ) > 0)
      {
         // Sheep maintain plan
         if (sheepLimit > 0)
         {
            if (sheepMaintain < 0)
            {
               sheepMaintain = createSimpleMaintainPlan(cUnitTypeSheep, sheepLimit, 
                  true, kbBaseGetMainID(cMyID), 1);
               aiPlanSetVariableInt(sheepMaintain, cTrainPlanNumberToMaintain, 0, sheepLimit);
               aiPlanSetActive(sheepMaintain);
            }
            aiPlanSetDesiredPriority(sheepMaintain, herdablePriority);
         }
         
         // Cow maintain plan
         if (cowLimit > 0)
         {
            if (cowMaintain < 0)
            {
               cowMaintain = createSimpleMaintainPlan(cUnitTypeCow, cowLimit, 
                  true, kbBaseGetMainID(cMyID), 1);
               aiPlanSetVariableInt(cowMaintain, cTrainPlanNumberToMaintain, 0, cowLimit);
               aiPlanSetActive(cowMaintain);
            }
            aiPlanSetDesiredPriority(cowMaintain, herdablePriority);
         }
         
         // Llama maintain plan
         if (llamaLimit > 0)
         {
            if (llamaMaintain < 0)
            {
               llamaMaintain = createSimpleMaintainPlan(cUnitTypeLlama, llamaLimit, 
                  true, kbBaseGetMainID(cMyID), 1);
               aiPlanSetVariableInt(llamaMaintain, cTrainPlanNumberToMaintain, 0, llamaLimit);
               aiPlanSetActive(llamaMaintain);
            }
            aiPlanSetDesiredPriority(llamaMaintain, herdablePriority);
         }
      }
      else if (kbUnitCount(cMyID, gLivestockPenUnit, cUnitStateABQ) < 1)
      {
         createSimpleBuildPlan(gLivestockPenUnit, 1, 65, true, cEconomyEscrowID, kbBaseGetMainID(cMyID), 1);
         
         if (sheepMaintain >= 0)
         {
            aiPlanDestroy(sheepMaintain);
            sheepMaintain = -1;
         }
         if (cowMaintain >= 0)
         {
            aiPlanDestroy(cowMaintain);
            cowMaintain = -1;
         }
         if (llamaMaintain >= 0)
         {
            aiPlanDestroy(llamaMaintain);
            llamaMaintain = -1;
         }
      }
   }
   else
   {
      if (kbUnitCount(cMyID, gLivestockPenUnit, cUnitStateABQ) > 1)
      {
         // Herdable maintain plan
         if (gMaxHerdablesMaintain < 0)
         {
            int herdableLimit = kbGetBuildLimit(cMyID, cUnitTypeHerdable);
            
            gMaxHerdablesMaintain = createSimpleMaintainPlan(cUnitTypeHerdable, herdableLimit, 
               true, kbBaseGetMainID(cMyID), 1);
            aiPlanSetVariableInt(gMaxHerdablesMaintain, cTrainPlanNumberToMaintain, 0, herdableLimit);
            aiPlanSetActive(gMaxHerdablesMaintain);
         }
         aiPlanSetDesiredPriority(gMaxHerdablesMaintain, herdablePriority);
      }
      else if (kbUnitCount(cMyID, gLivestockPenUnit, cUnitStateABQ) < 1)
      {
         createSimpleBuildPlan(gLivestockPenUnit, 1, 65, true, cEconomyEscrowID, kbBaseGetMainID(cMyID), 1);
         
         if (gMaxHerdablesMaintain >= 0)
         {
            aiPlanDestroy(gMaxHerdablesMaintain);
            gMaxHerdablesMaintain = -1;
         }
      }
   }
}
//==============================================================================
// millManager
// Make sure we have at least one mill at all times.
//==============================================================================
rule millManager
inactive
minInterval 40
{
    if ((kbUnitCount(cMyID, gFarmUnit, cUnitStateABQ) < 1) && (kbGetAge() >= cAge4))
    {
        createSimpleBuildPlan(gFarmUnit, 1, 70, true, cEconomyEscrowID, kbBaseGetMainID(cMyID), 1);
    }
    else
    {
        return;
    }
}
//==============================================================================
/* leader_suleiman.xs */
//==============================================================================

bool gSuleimanRulesEnabled = false;

void initLeaderSuleiman(void)
{
   aiEcho("Legendary Leaders: activating Suleiman the Magnificent personality.");

   llSetBalancedPersonality();
   btRushBoom = 0.4;
   btOffenseDefense = 0.6;
   btBiasTrade = 0.4;
   btBiasNative = 0.2;
   llSetMilitaryFocus(0.4, -0.2, 0.6);
   cvMaxTowers = 4;
   gSuleimanRulesEnabled = true;
}

rule suleimanGunpowderEmpire
inactive
minInterval 75
{
   if (gSuleimanRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasArt = 0.8;
      btBiasInf = 0.5;
   }
}

void enableLeaderSuleimanRules(void)
{
   if (gSuleimanRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("suleimanGunpowderEmpire");
}

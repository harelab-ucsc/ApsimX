﻿using System;

namespace Models.PMF.Phen
{
    /// <summary>
    /// 
    /// </summary>
    [Serializable]
    public class PhaseChangedType : EventArgs
    {
        /// <summary>The stage at phase change</summary>
        public String StageName = "";
        /// <summary>The stage number at phase change</summary>
        public double StageNumber = "";
    }
}

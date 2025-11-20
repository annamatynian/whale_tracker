# 📖 Onboarding Checklist for New Conversation

## ⚡ Quick Start (5 minutes)

Use this checklist at the beginning of each new conversation to ensure full context and proper methodology.

### 📋 Step 1: Core Methodology (2 minutes)
- [ ] **Read DEVELOPMENT_METHODOLOGY.md** - Essential principles
  - [ ] ✅ Small, testable modules approach
  - [ ] ✅ Avoid debugging hell (>30 min = rollback)
  - [ ] ✅ MVP first, add complexity gradually
  - [ ] ✅ Commit before major changes

### 📋 Step 2: **CRITICAL - Verify Real Project Status (2 minutes)**
- [ ] **🔍 Run `python verify_status.py`** - Get objective implementation status
  - [ ] ✅ Check which components actually work vs documented
  - [ ] ✅ Identify critical implementation gaps
  - [ ] ✅ Verify on-chain integration status
  - [ ] ✅ Confirm API integrations are working

**⚠️ NEVER trust documentation alone - always verify with code analysis**

### 📋 Step 3: Project Context (1 minute)  
- [ ] **Scan PROJECT_CONTEXT.md** - Current state understanding
  - [ ] ✅ LP Health Tracker = DeFi IL monitoring agent
  - [ ] ✅ Known gaps: NetPnLCalculator missing, on-chain gas costs missing
  - [ ] ✅ Architecture: Some components working, some have import errors
  - [ ] ✅ Goal: Professional portfolio + freelance preparation

## 🎯 Development Readiness Check

### **Before Starting Any Work:**
- [ ] **🔍 MANDATORY: Run `python verify_status.py`** - Know real status
- [ ] **Identify next small step** - What's the minimal next module?
- [ ] **Check critical gaps** - Are we fixing import errors or adding features?
- [ ] **Plan commit strategy** - When to save state?

### **Evidence-Based Assessment:**
- [ ] 🎯 **Focus on verified working components** - Build on solid foundation
- [ ] 🔬 **Fix critical gaps first** - NetPnLCalculator, gas costs
- [ ] 🛡️ **Don't assume documentation accuracy** - Code is the truth
- [ ] 🧪 **Test integration points** - Verify components work together

## 🚨 Anti-Patterns to Avoid

### ❌ Never Do:
- [ ] **Trust status documentation** without code verification
- [ ] **Plan features** without understanding current gaps
- [ ] **Debug for >30 minutes** without rollback consideration
- [ ] **Add complexity** before fixing existing import errors
- [ ] **Skip verify_status.py** - Always run it first

### ✅ Always Do:
- [ ] **Verify implementation status** with verify_status.py
- [ ] **Focus on critical gaps** - Fix import errors before new features
- [ ] **Test after changes** - Ensure components integrate properly
- [ ] **Small, testable changes** - One issue at a time
- [ ] **Evidence-based planning** - Build on what actually works

## 📊 Quick Project State Check

### **Essential Commands for Real Status:**
```bash
# MOST IMPORTANT - Run this first in every conversation
python verify_status.py

# Check import errors in components  
python -c "from src.simple_multi_pool import SimpleMultiPoolManager"

# Verify core IL calculation works
python -c "from src.data_analyzer import ImpermanentLossCalculator; print('IL Calculator OK')"

# Test live API integration
python -c "from src.data_providers import LiveDataProvider; print('Live APIs OK')"

# Check git status for context
git log --oneline -3
git status
```

### **Status Verification Results Interpretation:**

**🟢 Ready for New Features:**
- ✅ verify_status.py shows >80% checks passing
- ✅ No critical import errors
- ✅ Core components working

**🟡 Ready for Integration Work:**
- ⚠️ verify_status.py shows missing components
- ⚠️ Import errors in multi-pool manager
- ✅ Core mathematical functions working

**🔴 Need Critical Fixes First:**
- ❌ verify_status.py shows major gaps
- ❌ Multiple import failures
- ❌ Core workflow broken

## 🎯 Common Starting Points

### **When Status Shows Critical Gaps:**
1. **Fix import errors first** - Implement missing classes
2. **Verify basic workflow** - Ensure components integrate
3. **Add one small feature** - Build on working foundation
4. **Re-run verify_status.py** - Confirm improvements

### **When Status Shows Working Foundation:**
1. **Add missing on-chain integration** - Gas cost tracking
2. **Enhance existing features** - Improve working components
3. **Add new protocols** - Extend successful patterns
4. **Improve testing coverage** - Strengthen reliability

### **When Debugging Issues:**
1. **Time limit: 30 minutes max**
2. **Run verify_status.py** - Understand current baseline
3. **Check for import errors** - Often the root cause
4. **Consider rollback** if stuck
5. **Ask for help** with specific verification results

## 📞 Emergency Protocols

### **When verify_status.py Shows Critical Issues:**
- [ ] **Don't add new features** - Fix foundation first
- [ ] **Focus on import errors** - Usually NetPnLCalculator missing
- [ ] **Check Web3 integration gaps** - On-chain functionality missing
- [ ] **Verify basic components work** - IL calculations, data providers

### **When Components Have Import Errors:**
- [ ] **Check missing classes** - NetPnLCalculator commonly missing
- [ ] **Verify circular imports** - Common in complex projects
- [ ] **Test components individually** - Isolate working parts
- [ ] **Fix one import at a time** - Avoid complexity

---

## ✅ Onboarding Complete

**Once this checklist is complete, you should have:**
- ✅ **Objective understanding** of real implementation status
- ✅ **Evidence-based planning** approach using verify_status.py
- ✅ **Critical gaps identified** - NetPnLCalculator, gas costs
- ✅ **Safe development practices** with rollback safety
- ✅ **Ready to fix critical gaps** or build on working foundation

**🚀 Ready to continue development with accurate status understanding!**

---

## 🔍 **KEY PRINCIPLE FOR ALL CONVERSATIONS**

**📊 ALWAYS START WITH: `python verify_status.py`**

This provides objective, evidence-based understanding of:
- What's actually implemented vs documented
- Which APIs are working
- Critical implementation gaps
- Ready components vs broken imports

**Never make assumptions about project status based on documentation alone.**

---

**⏰ Total time: ~5 minutes | 💪 Result: Accurate project understanding and safe development practices**

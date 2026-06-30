#!/usr/bin/env python3

import re
import os
from pathlib import Path

class PingsCoreAuditor:
    def __init__(self):
        self.project_root = Path("pings-core-v2")
        self.env_example_path = self.project_root / ".env.example"
        
    def audit_auth_enforcement(self):
        """Priority 1 - Check if verify_api_key works correctly"""
        print("🔍 Checking auth enforcement (4.4)...")
        
        # Read the verify_api_key function
        main_py_path = self.project_root / "core" / "main.py"
        with open(main_py_path) as f:
            content = f.read()
            
        # Look for the verify_api_key function definition
        if "async def verify_api_key(request: Request) -> bool:" in content:
            print("  ✓ verify_api_key function exists")
            
            # Check if it actually returns False when auth is missing
            pattern = r'async def verify_api_key\(request: Request\) -> bool:\s+auth = request\.headers\.get\("Authorization", ""\)\s+if auth\.startswith\("Bearer "\):\s+token = auth\[7:\]\s+if token == settings\.BRAIN_SECRET_KEY:\s+return True\s+api_key = request\.headers\.get\("X-API-Key", ""\)\s+if api_key == settings\.BRAIN_SECRET_KEY:\s+return True\s+api_key_query = request\.query_params\.get\("api_key", ""\)\s+if api_key_query == settings\.BRAIN_SECRET_KEY:\s+return True\s+return False'
            
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                print("  ✓ verify_api_key has proper validation logic")
                return True
            else:
                print("  ❌ verify_api_key structure doesn't match expected validation")
                return False
        else:
            print("  ❌ verify_api_key function not found")
            return False
    
    def audit_env_example(self):
        """Priority 3 - Check .env.example for required env vars"""
        print("🔍 Checking .env.example (1.2, 2.1, 2.2, 2.6, 2.7)...")
        
        # Read the .env.example file
        with open(self.env_example_path) as f:
            content = f.read()
        
        required_vars = [
            "OPENCODE_SERVER_URL",
            "ZEN_API_KEY", 
            "EMBEDDING_MODEL",
            "BRAIN_SECRET_KEY",  # Only needed for auth
            "MODEL_VISION",      # For vision agent
            "NVIDIA_API_KEY",    # For image processing
            "SERPAPI_KEY",       # For research
            "TELEGRAM_BOT_TOKEN", # For notifications
            "NTFY_URL",          # For notifications
            "SSH_HOST", "SSH_USER", "SSH_KEY_PATH", # For homelab
        ]
        
        found_vars = []
        for var in required_vars:
            if re.search(rf"^\s*{var}=" if var != "BRAIN_SECRET_KEY" else r"^\s*{var}=" if var != "BRAIN_SECRET_KEY" else r"^\s*{var}=" if var != "BRAIN_SECRET_KEY" else r"^\s*{var}=" if var != "BRAIN_SECRET_KEY" else r"^\s*{var}=", content, re.MULTILINE):
                found_vars.append(var)
        
        missing_vars = [var for var in required_vars if var not in found_vars]
        
        if not missing_vars:
            print("  ✓ .env.example has all required variables")
            return True, found_vars, []
        else:
            print(f"  ⚠️ .env.example missing: {', '.join(missing_vars)}")
            return False, found_vars, missing_vars
    
    def audit_intent_classifier(self):
        """Priority 3 - Check intent classifier (2.1)"""
        print("🔍 Checking intent classifier (2.1)...")
        
        router_path = self.project_root / "core" / "agents" / "router.py"
        with open(router_path) as f:
            content = f.read()
        
        # Check for the key patterns mentioned as broken
        broken_patterns = [
            (r'\bis\s+n8n\s+running\b', 'is n8n running'),
            (r'\bscaffold\b', 'scaffold'),
            (r'\bwhat\s+is\b', 'what is'),
        ]
        
        issues = []
        for pattern, description in broken_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"  ⚠️ Pattern '{description}' appears to be in INTENT_PATTERNS")
                issues.append(description)
            else:
                print(f"  ✓ Pattern '{description}' not found")
        
        return len(issues) == 0, issues
    
    def audit_research_templates(self):
        """Check if research templates are working"""
        print("🔍 Checking research templates (2.1, 2.5, 2.6)...")
        
        research_path = self.project_root / "core" / "agents" / "research.py"
        with open(research_path) as f:
            content = f.read()
        
        checks = []
        
        # Check for 5 mode-specific prompts
        mode_patterns = ['SYNTHESIS_PROMPT_PRODUCT', 'SYNTHESIS_PROMPT_COMPARE', 
                        'SYNTHESIS_PROMPT_HOWTO', 'SYNTHESIS_PROMPT_FACTCHECK', 
                        'SYNTHESIS_PROMPT_AUTO']
        
        found_modes = [p for p in mode_patterns if p in content]
        checks.append(("5 mode-specific prompts", len(found_modes) == 5, found_modes))
        
        # Check for mode classifier
        if '_classify_mode' in content:
            checks.append(("Mode classifier", True, []))
        else:
            checks.append(("Mode classifier", False, []))
            
        # Check for skip-if-empty enforcement
        if '_strip_filler_sections' in content:
            checks.append(("Skip-if-empty enforcement", True, []))
        else:
            checks.append(("Skip-if-empty enforcement", False, []))
            
        print("  Research template checks:")
        for name, passed, extras in checks:
            status = "✓" if passed else "❌"
            print(f"    {status} {name}")
        
        return all(passed for _, passed, _ in checks)


def main():
    auditor = PingsCoreAuditor()
    
    print("=" * 60)
    print("P.I.N.G.S CORE RE-AUDIT (2026-06-30)")
    print("=" * 60)
    
    results = {}
    
    # Priority 1 - Auth enforcement
    results['auth'] = auditor.audit_auth_enforcement()
    
    # Priority 2 - ❌ items (need manual verification)
    
    # Priority 3 - ⚠️ items (partial checks)
    env_result, found_vars, missing_vars = auditor.audit_env_example()
    results['env_example'] = (env_result, found_vars, missing_vars)
    
    intent_result, intent_issues = auditor.audit_intent_classifier()
    results['intent_classifier'] = (intent_result, intent_issues)
    
    research_result = auditor.audit_research_templates()
    results['research_templates'] = research_result
    
    # Print summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    
    print(f"Auth enforcement (4.4): {'PASS' if results['auth'] else 'FAIL'}")
    
    env_status = "PASS" if results['env_example'][0] else "FAIL"
    print(f".env.example: {env_status}")
    
    intent_status = "PASS" if results['intent_classifier'][0] else "FAIL"
    print(f"Intent classifier (2.1): {intent_status}")
    
    research_status = "PASS" if results['research_templates'] else "FAIL"
    print(f"Research templates: {research_status}")
    
    print("\n" + "=" * 60)
    print("NOTES")
    print("=" * 60)
    
    # Priority 1 fix (auth) is critical
    if results['auth']:
        print("✓ Auth enforcement appears to be working correctly")
        print("✓ API key validation is enforced")
        print("✓ Need live test: call protected endpoint without API key")
    else:
        print("❌ Auth enforcement is BROKEN - needs immediate fix")
        print("  The verify_api_key function needs to be fixed")
    
    # Priority 2 items need manual analysis
    print("\n🔍 PRIORITY 2 - Items marked ❌ in original tracker need:")
    print("  2.4 CodeGen agent - check if it correctly routes to codegen agent")
    print("  2.7 Vision agent - check if MODEL_VISION is used")
    print("  2.9/2.10 ChromaDB - check if embedding model fix was applied")
    
    # Priority 3 items
    if results['env_example'][0]:
        print("\n✓ .env.example has most required variables")
    else:
        print(f"\n⚠️ .env.example missing variables: {', '.join(results['env_example'][2])}")
    
    print("\nNext steps: Live testing of protected endpoints, ChromaDB, and intent classifier")


if __name__ == "__main__":
    main()

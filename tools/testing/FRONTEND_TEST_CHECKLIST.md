# Frontend Manual Test Checklist

Comprehensive manual testing checklist for the DoD Contracting Frontend Application.

**Test URL:** http://localhost:5173  
**Test Credentials:**
- Email: `john.contracting@navy.mil`
- Password: `password123`

---

## 1. Authentication Flow

### 1.1 Login Page
- [ ] Page loads without errors
- [ ] Email field accepts input
- [ ] Password field masks input
- [ ] "Login" button is clickable
- [ ] Error message shows for invalid credentials
- [ ] Successful login redirects to dashboard
- [ ] Loading indicator shows during login

### 1.2 Session Management
- [ ] User stays logged in on page refresh
- [ ] Logout button works correctly
- [ ] Session expires after inactivity (if configured)
- [ ] Protected routes redirect to login when not authenticated

---

## 2. Dashboard/Home

### 2.1 Project List
- [ ] Dashboard loads after login
- [ ] Existing projects display correctly
- [ ] "New Project" button is visible
- [ ] Project cards show correct information
- [ ] Click on project navigates to project details

### 2.2 Navigation
- [ ] Sidebar navigation works
- [ ] All menu items are clickable
- [ ] Active page is highlighted
- [ ] Mobile menu works (if applicable)

---

## 3. Project Management

### 3.1 Create Project
- [ ] "New Project" dialog opens
- [ ] Form fields are displayed
  - [ ] Project name
  - [ ] Description
  - [ ] Organization
  - [ ] Estimated value
  - [ ] Contract type
- [ ] Required field validation works
- [ ] Cancel button closes dialog
- [ ] Submit creates project and shows success
- [ ] New project appears in project list

### 3.2 Project Details
- [ ] Project details page loads
- [ ] Project information displays correctly
- [ ] Phases are shown
- [ ] Documents list is displayed
- [ ] Edit project button works
- [ ] Delete project button works (with confirmation)

### 3.3 Phase Display
- [ ] All 4 phases display (Pre-Solicitation, Solicitation, Post-Solicitation, Award)
- [ ] Phase status shows correctly
- [ ] Steps within phases are visible
- [ ] Phase progress indicators work

---

## 4. Document Generation

### 4.1 Quick Generate
- [ ] "Quick Generate" option is available
- [ ] Assumptions form displays
- [ ] All assumption fields can be filled
- [ ] "Generate" button starts generation
- [ ] Progress indicator shows during generation
- [ ] Generated documents appear in list
- [ ] Error handling works if generation fails

### 4.2 Individual Document Generation
- [ ] Document generation button works per document
- [ ] Generation progress shows
- [ ] Generated content displays correctly
- [ ] Quality score shows after generation

---

## 5. Live Editor

### 5.1 Editor Loading
- [ ] Editor opens when clicking on document
- [ ] Content loads correctly
- [ ] Toolbar displays
- [ ] Sidebar panels display

### 5.2 Rich Text Editing
- [ ] Text can be typed/edited
- [ ] Bold formatting works
- [ ] Italic formatting works
- [ ] Headings work (H1, H2, H3)
- [ ] Bullet lists work
- [ ] Numbered lists work
- [ ] Undo/Redo works

### 5.3 Quality Score Panel (Right Sidebar)

#### Initial Load
- [ ] Quality score displays on load (from precomputed scores)
- [ ] Score shows as numeric value (0-100)
- [ ] Grade badge shows (A/B/C/D/F)
- [ ] "AI Verified" badge shows if score is fresh

#### After Editing
- [ ] Score badge changes to "Outdated" (amber) after editing
- [ ] "Re-analyze" button becomes enabled
- [ ] Score number still shows old value until re-analyzed

#### Re-analyze Button (NEW FEATURE)
- [ ] Button is disabled when score is fresh
- [ ] Button is enabled when section is edited (stale)
- [ ] Clicking button shows loading spinner
- [ ] Button text changes to "Analyzing..."
- [ ] After analysis completes:
  - [ ] New score displays
  - [ ] Badge changes back to "AI Verified" (green)
  - [ ] Button becomes disabled again
- [ ] Error message shows if analysis fails

#### Quality Breakdown (5 Categories)
- [ ] Hallucination score displays
- [ ] Vague Language score displays
- [ ] Citations score displays
- [ ] Compliance score displays
- [ ] Completeness score displays
- [ ] Progress bars update with scores

### 5.4 Issues Panel
- [ ] Issues list displays
- [ ] Clicking issue highlights text in editor
- [ ] Fix buttons work for applicable issues
- [ ] "Fix All" button works
- [ ] Issue count updates after fixes

### 5.5 Field Navigator
- [ ] Field navigator button is visible
- [ ] Clicking opens field navigator panel
- [ ] Fillable fields (TBD, underscores) are detected
- [ ] Navigation between fields works

### 5.6 Version History
- [ ] "Commit Version" button works
- [ ] Version history panel shows previous versions
- [ ] Compare versions works
- [ ] Restore version works

### 5.7 Save Functionality
- [ ] Save button is visible
- [ ] Save shows loading state
- [ ] Save shows success notification
- [ ] Content persists after page refresh

---

## 6. Export Functionality

### 6.1 Export Dialog
- [ ] Export button opens dialog
- [ ] PDF option is available
- [ ] DOCX option is available

### 6.2 Compliance Gate
- [ ] Compliance check runs before export
- [ ] Compliance status shows
- [ ] Can proceed with export if compliant
- [ ] Warning shows if compliance issues exist

### 6.3 File Download
- [ ] PDF export downloads file
- [ ] DOCX export downloads file
- [ ] File contains correct content
- [ ] File opens correctly in appropriate application

---

## 7. Approval Workflow

### 7.1 Request Approval
- [ ] "Request Approval" button is visible
- [ ] Dialog opens with approver selection
- [ ] Comments field works
- [ ] Submit creates approval request
- [ ] Status updates to "Pending Approval"

### 7.2 Approval Actions (if user is approver)
- [ ] Pending approvals list shows
- [ ] Approve button works
- [ ] Reject button works
- [ ] Comments required for rejection
- [ ] Status updates after action

### 7.3 Approval History
- [ ] History panel shows past approvals
- [ ] Timestamps display correctly
- [ ] Approver names show
- [ ] Comments are visible

---

## 8. Admin Features

### 8.1 User Management (Admin only)
- [ ] Admin menu is visible for admin users
- [ ] User list displays
- [ ] Create user form works
- [ ] Update user role works
- [ ] Delete user works (with confirmation)

### 8.2 System Settings
- [ ] Settings page loads
- [ ] Configuration options display
- [ ] Changes save correctly

---

## 9. Responsive Design

### 9.1 Desktop (1920x1080)
- [ ] All elements visible
- [ ] No horizontal scrolling
- [ ] Proper spacing

### 9.2 Laptop (1366x768)
- [ ] All elements visible
- [ ] No overflow issues
- [ ] Readable text

### 9.3 Tablet (768x1024)
- [ ] Navigation adapts
- [ ] Content readable
- [ ] Touch targets adequate

---

## 10. Error Handling

### 10.1 Network Errors
- [ ] Error message shows when API is down
- [ ] Retry option available
- [ ] User-friendly error messages

### 10.2 Validation Errors
- [ ] Form validation shows inline errors
- [ ] Required field errors show
- [ ] Format validation works (email, etc.)

### 10.3 Generation Errors
- [ ] Error message shows if generation fails
- [ ] User can retry
- [ ] Partial progress is preserved

---

## 11. Performance

### 11.1 Page Load
- [ ] Dashboard loads in < 3 seconds
- [ ] Project details load in < 2 seconds
- [ ] Editor loads in < 3 seconds

### 11.2 Interactions
- [ ] No lag when typing in editor
- [ ] Buttons respond immediately
- [ ] Scrolling is smooth

---

## 12. Browser Compatibility

Test in each browser:

### Chrome
- [ ] All features work
- [ ] No console errors

### Firefox
- [ ] All features work
- [ ] No console errors

### Safari
- [ ] All features work
- [ ] No console errors

### Edge
- [ ] All features work
- [ ] No console errors

---

## Test Session Summary

| Category | Tests | Passed | Failed | Notes |
|----------|-------|--------|--------|-------|
| Authentication | 8 | | | |
| Dashboard | 6 | | | |
| Projects | 12 | | | |
| Documents | 6 | | | |
| Live Editor | 30+ | | | |
| Export | 6 | | | |
| Approvals | 10 | | | |
| Admin | 5 | | | |
| Responsive | 9 | | | |
| Errors | 6 | | | |
| Performance | 5 | | | |

**Tester:** ____________________  
**Date:** ____________________  
**Environment:** ____________________  
**Overall Status:** ⬜ Pass / ⬜ Fail

---

## Notes

Record any bugs, issues, or observations during testing:

1. _________________________________________________
2. _________________________________________________
3. _________________________________________________
4. _________________________________________________
5. _________________________________________________

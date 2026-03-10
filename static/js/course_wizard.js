/**
 * Course Creation Wizard — 3-step progressive form
 *
 * Steps:
 *   1. Basics (title, instrument, difficulty_level, genre)
 *   2. Details (description, prerequisites, estimated_duration_weeks, max_students, thumbnail)
 *   3. Review & Publish (read-only summary + is_published toggle + submit)
 *
 * The form is a single <form> wrapping all fields. Only the "Create Course"
 * button on step 3 actually submits. Steps are shown/hidden via CSS classes.
 */
(function () {
    'use strict';

    var currentStep = 1;
    var totalSteps = 3;

    // DOM references
    var stepPanels = [
        document.getElementById('wizard-step-1'),
        document.getElementById('wizard-step-2'),
        document.getElementById('wizard-step-3'),
    ];
    var stepIndicators = [
        document.getElementById('step-indicator-1'),
        document.getElementById('step-indicator-2'),
        document.getElementById('step-indicator-3'),
    ];
    var btnPrev = document.getElementById('wizard-btn-prev');
    var btnNext = document.getElementById('wizard-btn-next');
    var btnSubmit = document.getElementById('wizard-btn-submit');

    /**
     * Show the given step (1-indexed) and hide the others.
     */
    function showStep(n) {
        currentStep = n;

        // Show/hide panels
        for (var i = 0; i < totalSteps; i++) {
            if (stepPanels[i]) {
                stepPanels[i].classList.toggle('hidden', i !== n - 1);
            }
        }

        // Update step indicators
        for (var j = 0; j < totalSteps; j++) {
            if (stepIndicators[j]) {
                if (j < n - 1) {
                    // Completed steps
                    stepIndicators[j].setAttribute('data-content', '\u2713');
                    stepIndicators[j].className = 'step step-primary';
                } else if (j === n - 1) {
                    // Current step
                    stepIndicators[j].setAttribute('data-content', String(j + 1));
                    stepIndicators[j].className = 'step step-primary';
                } else {
                    // Future steps
                    stepIndicators[j].setAttribute('data-content', String(j + 1));
                    stepIndicators[j].className = 'step';
                }
            }
        }

        // Show/hide navigation buttons
        btnPrev.classList.toggle('hidden', n === 1);
        btnNext.classList.toggle('hidden', n === totalSteps);
        btnSubmit.classList.toggle('hidden', n !== totalSteps);

        // If on review step, build the summary
        if (n === totalSteps) {
            updateReview();
        }

        // Scroll to top of form
        var wizardContainer = document.getElementById('course-wizard');
        if (wizardContainer) {
            wizardContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /**
     * Validate the current step before advancing.
     * Returns true if valid, false otherwise.
     */
    function validateStep(n) {
        if (n === 1) {
            var titleField = document.getElementById('id_title');
            if (!titleField || !titleField.value.trim()) {
                // Show inline error
                showFieldError(titleField, 'Please enter a course title.');
                titleField.focus();
                return false;
            }
            clearFieldError(titleField);
            return true;
        }
        // Step 2 has no required client-side validation (all optional or have defaults)
        return true;
    }

    /**
     * Show an inline error message below a field.
     */
    function showFieldError(field, message) {
        clearFieldError(field);
        if (!field) return;
        var errorLabel = document.createElement('label');
        errorLabel.className = 'label';
        errorLabel.innerHTML = '<span class="label-text-alt text-error">' + message + '</span>';
        errorLabel.setAttribute('data-wizard-error', 'true');
        field.classList.add('input-error');
        field.parentNode.appendChild(errorLabel);
    }

    /**
     * Clear inline error from a field.
     */
    function clearFieldError(field) {
        if (!field) return;
        field.classList.remove('input-error');
        var parent = field.parentNode;
        var errors = parent.querySelectorAll('[data-wizard-error]');
        for (var i = 0; i < errors.length; i++) {
            errors[i].remove();
        }
    }

    /**
     * Build the review summary on step 3 from current form values.
     */
    function updateReview() {
        var reviewBody = document.getElementById('review-summary');
        if (!reviewBody) return;

        var title = getFieldValue('id_title');
        var instrument = getFieldValue('id_instrument');
        var difficultySelect = document.getElementById('id_difficulty_level');
        var difficulty = difficultySelect ? difficultySelect.options[difficultySelect.selectedIndex].text : '';
        var genre = getFieldValue('id_genre');
        var description = getFieldDisplayValue('id_description');
        var prerequisites = getFieldValue('id_prerequisites');
        var duration = getFieldValue('id_estimated_duration_weeks');
        var maxStudents = getFieldValue('id_max_students');
        var thumbnailInput = document.getElementById('id_thumbnail');
        var thumbnailName = (thumbnailInput && thumbnailInput.files && thumbnailInput.files.length > 0)
            ? thumbnailInput.files[0].name
            : 'None';

        var html = '';
        html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">';

        html += reviewItem('Title', title || '<span class="text-error">Required</span>');
        html += reviewItem('Instrument', instrument || '<span class="text-base-content/50">Not set</span>');
        html += reviewItem('Difficulty', difficulty);
        html += reviewItem('Genre', genre || '<span class="text-base-content/50">Not set</span>');
        html += reviewItem('Duration', (duration || '8') + ' weeks');
        html += reviewItem('Max Students', maxStudents || '30');
        html += reviewItem('Thumbnail', thumbnailName);

        html += '</div>';

        if (prerequisites) {
            html += '<div class="mt-4">';
            html += '<h4 class="font-semibold text-sm text-base-content/70 mb-1">Prerequisites</h4>';
            html += '<p class="text-sm">' + escapeHtml(prerequisites) + '</p>';
            html += '</div>';
        }

        if (description) {
            html += '<div class="mt-4">';
            html += '<h4 class="font-semibold text-sm text-base-content/70 mb-1">Description</h4>';
            html += '<div class="text-sm prose prose-sm max-w-none bg-base-200 rounded-lg p-3">' + description + '</div>';
            html += '</div>';
        }

        reviewBody.innerHTML = html;
    }

    function reviewItem(label, value) {
        return '<div>'
            + '<span class="text-xs font-semibold text-base-content/50 uppercase tracking-wide">' + label + '</span>'
            + '<p class="font-medium">' + value + '</p>'
            + '</div>';
    }

    function getFieldValue(id) {
        var el = document.getElementById(id);
        return el ? el.value.trim() : '';
    }

    /**
     * Get display value for TinyMCE or textarea fields.
     * TinyMCE replaces the textarea with an iframe, so we try to get content from TinyMCE first.
     */
    function getFieldDisplayValue(id) {
        // Try TinyMCE editor
        if (typeof tinyMCE !== 'undefined') {
            var editor = tinyMCE.get(id);
            if (editor) {
                return editor.getContent();
            }
        }
        // Fall back to textarea value
        var el = document.getElementById(id);
        return el ? escapeHtml(el.value.trim()) : '';
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    // Event listeners
    if (btnNext) {
        btnNext.addEventListener('click', function () {
            if (validateStep(currentStep)) {
                showStep(currentStep + 1);
            }
        });
    }

    if (btnPrev) {
        btnPrev.addEventListener('click', function () {
            showStep(currentStep - 1);
        });
    }

    // On form submit, sync TinyMCE content back to textarea
    var form = document.getElementById('course-wizard-form');
    if (form) {
        form.addEventListener('submit', function () {
            if (typeof tinyMCE !== 'undefined') {
                tinyMCE.triggerSave();
            }
        });
    }

    // Handle server-side validation errors: find the first field with an error
    // and switch to its step
    function findStepWithErrors() {
        var step1Fields = ['id_title', 'id_instrument', 'id_difficulty_level', 'id_genre'];
        var step2Fields = ['id_description', 'id_prerequisites', 'id_estimated_duration_weeks', 'id_max_students', 'id_thumbnail'];

        // Check for Django error labels (label-text-alt text-error)
        for (var i = 0; i < step1Fields.length; i++) {
            var field = document.getElementById(step1Fields[i]);
            if (field) {
                var formControl = field.closest('.form-control');
                if (formControl && formControl.querySelector('.text-error')) {
                    return 1;
                }
            }
        }
        for (var j = 0; j < step2Fields.length; j++) {
            var field2 = document.getElementById(step2Fields[j]);
            if (field2) {
                var formControl2 = field2.closest('.form-control');
                if (formControl2 && formControl2.querySelector('.text-error')) {
                    return 2;
                }
            }
        }

        // Check for non-field errors (alert-error at top)
        var nonFieldErrors = document.querySelector('#course-wizard .alert-error');
        if (nonFieldErrors) {
            return 1;
        }

        return 0; // No errors found
    }

    // Initialize: show step 1 (or the step with errors if re-rendered after validation failure)
    var errorStep = findStepWithErrors();
    showStep(errorStep > 0 ? errorStep : 1);
})();

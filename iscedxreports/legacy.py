def get_student_grade_summary_data(
        request, course, get_grades=True, get_raw_scores=False,
        use_offline=False, get_score_max=False
):
    """
    Return data arrays with student identity and grades for specified course.
    course = CourseDescriptor
    course_key = course ID
    Note: both are passed in, only because instructor_dashboard already has them already.
    returns datatable = dict(header=header, data=data)
    where
    header = list of strings labeling the data fields
    data = list (one per student) of lists of data corresponding to the fields
    If get_raw_scores=True, then instead of grade summaries, the raw grades for all graded modules are returned.
    If get_score_max is True, two values will be returned for each grade -- the
    total number of points earned and the total number of points possible. For
    example, if two points are possible and one is earned, (1, 2) will be
    returned instead of 0.5 (the default).
    """
    course_key = course.id
    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1,
    ).prefetch_related("groups").order_by('username')

    header = [_('ID'), _('Username'), _('Full Name'), _('edX email'), _('External email')]

    datatable = {'header': header, 'students': enrolled_students}
    data = []

    gtab = GradeTable()

    for student in enrolled_students:
        datarow = [student.id, student.username, student.profile.name, student.email]
        try:
            datarow.append(student.externalauthmap.external_email)
        except Exception:  # pylint: disable=broad-except
            datarow.append('')

        if get_grades:
            gradeset = student_grades(student, request, course, keep_raw_scores=get_raw_scores, use_offline=use_offline)
            log.debug(u'student=%s, gradeset=%s', student, gradeset)
            with gtab.add_row(student.id) as add_grade:
                if get_raw_scores:
                    # The following code calls add_grade, which is an alias
                    # for the add_row method on the GradeTable class. This adds
                    # a grade for each assignment. Depending on whether
                    # get_score_max is True, it will return either a single
                    # value as a float between 0 and 1, or a two-tuple
                    # containing the earned score and possible score for
                    # the assignment (see docstring).
                    for score in gradeset['raw_scores']:
                        if get_score_max is True:
                            add_grade(score.section, score.earned, score.possible)
                        else:
                            add_grade(score.section, score.earned)
                else:
                    for grade_item in gradeset['section_breakdown']:
                        add_grade(grade_item['label'], grade_item['percent'])
            student.grades = gtab.get_grade(student.id)

        data.append(datarow)

    # if getting grades, need to do a second pass, and add grades to each datarow;
    # on the first pass we don't know all the graded components
    if get_grades:
        for datarow in data:
            # get grades for student
            sgrades = gtab.get_grade(datarow[0])
            datarow += sgrades

        # get graded components and add to table header
        assignments = gtab.get_graded_components()
        header += assignments
        datatable['assignments'] = assignments

    datatable['data'] = data
    return datatable

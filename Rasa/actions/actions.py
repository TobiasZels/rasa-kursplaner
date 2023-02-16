##################################################################################
#  You can add your actions in this file or create any other file in this folder #
##################################################################################
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, ReminderScheduled, ConversationPaused, ConversationResumed, FollowupAction, Restarted, ReminderScheduled
from rasa_sdk.executor import CollectingDispatcher

mainSubject = ""
graduation = ""
subSubject = ""
semesterCount = ""
finishedModules = []
finishedCourses = []
maxStudyLength = ""
sws = ""

class ValidateMainSubject(Action):

    def name(self):
        return 'action_get_main_subject'

    def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        mainSubject = tracker.get_slot("subjects")
        
        #return [SlotSet("main_set", "true"), SlotSet("main_subject", "wahr"), SlotSet("more_graduations", "true")]
        return [SlotSet("main_set", "true"), SlotSet('main_subject', mainSubject), SlotSet("more_graduations", "false")]

class FetchMainSubject(Action):
    def name(self):
        return 'action_fetch_main_subject'

    def run(self, dispatcher, tracker, domain):

        return [SlotSet('main_subject', mainSubject)]

class SubSubjectNeeded(Action):

    def name(self):
        return 'action_sub_subject_needed'

    def run(self, dispatcher, tracker, domain):
        
        return [SlotSet("sub_subject_needed", False)]

class ValidateSubSubject(Action):

    def name(self):
        return 'action_validate_sub_subject'

    def run(self, dispatcher, tracker, domain):
        if tracker.get_slot("subjects"):
            subSubject = tracker.get_slot("subjects")
        
        return [SlotSet("sub_set", True), SlotSet("sub_subject", subSubject)]

class ValidateGraduation(Action):

    def name(self):
        return 'action_validate_graduation'

    def run(self, dispatcher, tracker, domain):
        graduation = tracker.get_slot("graduation")
        
        #return [SlotSet("main_set", "true"), SlotSet("main_subject", "wahr"), SlotSet("more_graduations", "true")]
        return [SlotSet("graduation_set", "true"), SlotSet("graduation", graduation)]


class FetchSemesterInfo(Action):

    def name(self):
        return 'action_fetch_semester_info'

    def run(self, dispatcher, tracker, domain):
        
        return [SlotSet("min_semester", "6"), SlotSet("max_semester", "9")]


class ValidateSemester(Action):

    def name(self):
        return 'action_validate_semester'

    def run(self, dispatcher, tracker, domain):
        semesterCount = tracker.get_slot("semester")
        return [SlotSet("semester_set", "true"), SlotSet("semester_count", semesterCount)]


class MaxSemesterLength(Action):

    def name(self):
        return 'action_max_semester_length'

    def run(self, dispatcher, tracker, domain):
        maxStudyLength = tracker.get_slot("semester")
        return [SlotSet("semester_set", "true"), SlotSet("sws_empf", "15"), SlotSet("semester_count", semesterCount)]

class SaveFinishedModules(Action):

    def name(self):
        return 'action_save_finished_modules'

    def run(self, dispatcher, tracker, domain):
        finishedModules = tracker.get_slot("modules")
        return [SlotSet("modules", finishedModules)]

class SaveFinishedCourses(Action):

    def name(self):
        return 'action_save_finished_courses'

    def run(self, dispatcher, tracker, domain):
        finishedCourses = tracker.get_slot("courses")
        return [SlotSet("courses", finishedCourses)]

class SaveSWS(Action):

    def name(self):
        return 'action_save_sws'

    def run(self, dispatcher, tracker, domain):
        sws = tracker.get_slot("sws")
        return [SlotSet("sws", sws)]


class CheckNextCourse(Action):

    def name(self):
        return 'action_fetch_next_course'

    def run(self, dispatcher, tracker, domain):
        value = False
        tracker.get_slot("sws")
        return [SlotSet("course_list_empty", value)]
        #, SlotSet("multiple_courses", False)


class CheckChosenCourse(Action):
    def name(self):
        return 'action_check_chosen_courses'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("courses_selected", "true")]

class FetchCourse(Action):
    def name(self):
        return 'action_fetch_course'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("next_course", "Kurs1"), SlotSet("next_module", "Modul 1"), SlotSet("speciality_bool", "false"), SlotSet("speciality_text", "None")]
        
class FetchCourseList(Action):
    def name(self):
        return 'action_fetch_course_list'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("next_course_list", ["Kurs1", "Kurs2"]), SlotSet("next_module", "Modul 1")]

class UserAcceptsCourse(Action):
    def name(self):
        return 'action_user_accepts_course'

    def run(self, dispatcher, tracker, domain):
        return 

class UserRejectsCourse(Action):
    def name(self):
        return 'action_user_rejects_course'

    def run(self, dispatcher, tracker, domain):
        return 

class TakeSelectedCourse(Action):
    def name(self):
        return 'action_user_takes_selected_course'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("course_exists", "false"), SlotSet("next_course", "Kurs 1")]

class GetSelectedCourse(Action):
    def name(self):
        return 'action_user_get_selected_course'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("course_exists", "false"), SlotSet("next_course", "Kurs 1")]

class GetConnectedCourses(Action):
    def name(self):
        return 'action_connected_courses'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("connected_courses_exist", "false"), SlotSet("next_course", "Kurs1"), SlotSet("next_module", "Modul 1"), SlotSet("speciality_bool", "true"), SlotSet("speciality_text", "None")]

class CheckSWS(Action):
    def name(self):
        return 'action_check_sws'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("sws_full", "false"), SlotSet("near_max_lp", "false"), SlotSet("lp_left", "15")]

class GetSchedule(Action):
    def name(self):
        return 'action_get_schedule'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("schedule_link", "pdf")]

class FetchInformation(Action):
    def name(self):
        return 'action_fetch_information'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("add_information", "pdf"), SlotSet("add_information_exists", "true")]

class ChangeSchedule(Action):
    def name(self):
        return 'action_change_schedule'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("course_exists", "true"), SlotSet("course_delete", "true"), SlotSet("next_course", "Kurs 1"), SlotSet("warning", "blabla")]
'use strict';


var billsApp = angular.module('billsApp', [
    'ngRoute',
    'billsAppControllers',
    'menuBarAppControllers',
    'jlareau.pnotify',
    'dbServices',
    'feedbackServices',
    'ui.bootstrap',
    'formly',
    'formlyBootstrap',
    'xeditable',
    'ngAnimate'
]);


billsApp.run(function() {
    FastClick.attach(document.body);
});


billsApp.run(function(editableOptions) {
  editableOptions.theme = 'bs3'; // bootstrap3 theme. Can be also 'bs2', 'default'
});


billsApp.config(['$routeProvider', 'notificationServiceProvider', function($routeProvider, notificationServiceProvider) {
    $routeProvider.
    when('/billPrep', {
        templateUrl: '/static/partials/billPrep.html',
        controller: ''
    }).
    when('/userAccount', {
        templateUrl: '/static/partials/userAccount.html',
        controller: ''
    }).
    otherwise({
        redirectTo: '/billPrep'
    });
    notificationServiceProvider.setStack('bottom_right', 'stack-bottomright', {
                dir1: 'up',
                dir2: 'left',
                firstpos1: 25,
                firstpos2: 25
            })
    notificationServiceProvider.setDefaultStack('bottom_right');

}]);


billsApp.directive('ngReallyClick', [function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            element.bind('click', function() {
                var message = attrs.ngReallyMessage;
                if (message && confirm(message)) {
                    scope.$apply(attrs.ngReallyClick);
                }
            });
        }
    }
}]);



var loginApp = angular.module('loginApp', [
    'ngRoute',
    'loginAppControllers',
    'loginServices',
    'jlareau.pnotify',
    'formly',
    'formlyBootstrap'
]);


loginApp.config(['$routeProvider', function($routeProvider) {
    $routeProvider.
    when('/login', {
        templateUrl: '/static/partials/loginAppLoginView.html',
        controller: 'loginAppLoginController'
    }).
    when('/register', {
        templateUrl: '/static/partials/loginAppRegisterView.html',
        controller: 'loginAppRegisterController'
    }).
    otherwise({
        templateUrl: '/static/partials/loginAppLoginView.html',
        controller: 'loginAppLoginController'
    });
}]);



/*********************
*  Database Services *
**********************/

var dbServices = angular.module('dbServices', ['ngResource']);

dbServices.factory('Bill', ['$resource',
  function($resource){
    return $resource('/api/bill/:billId', {}, {
      'query': {method:'GET', isArray:false},
      'get': {method:'GET', params:{billId:'billId'}, isArray:false},
      'create': {method:'POST', params:{billId:'billId'}, isArray:false},
      'update': {method:'PUT', isArray:false},
      'delete': {method:'DELETE', isArray:false}
    });
  }]);

dbServices.factory('PaymentPlan', ['$resource',
  function($resource){
    return $resource('/api/payment_plan/:payment_plan_id', {}, {
      'query': {method:'GET', isArray:false},
      'get': {method:'GET', params:{payment_plan_id:'payment_plan_id'}, isArray:false},
      'create': {method:'POST', params:{payment_plan_id:'payment_plan_id'}, isArray:false},
      'update': {method:'PUT', isArray:false},
      'delete': {method:'DELETE', isArray:false}
    });
  }]);

dbServices.factory('Me', ['$resource',
  function($resource){
    return $resource('/api/me/:userId', {}, {
      'query': {method:'GET', isArray:false},
      'get': {method:'GET', params:{userId:'users'}, isArray:false},
      'update': {method:'PUT', isArray:false}
    });
  }]);



/******************
*  Login Services *
******************/

var loginServices = angular.module('loginServices', ['ngResource']);

loginServices.factory('Login', ['$resource',
  function($resource){
    return $resource('/api/login/', {}, {
      'save': {method:'POST', isArray:false}
    });
  }]);

loginServices.factory('LoginCheck', ['$resource',
  function($resource){
    return $resource('/api/login_check/', {}, {
      'get': {method:'GET', isArray:false}
    });
  }]);


/*********************
*  Feedback Services *
*********************/

var feedbackServices = angular.module('feedbackServices', ['ngResource']);

feedbackServices.factory('Feedback', ['$resource',
  function($resource){
    return $resource('/api/feedback/', {}, {
      'query': {method:'GET', isArray:false},
      'get': {method:'GET', params:{userId:'users'}, isArray:false},
      'create': {method:'POST', isArray:false}
    });
  }]);

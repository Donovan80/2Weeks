'use strict';

var myApp = angular.module('myApp', [
    'ngRoute',
    'userControllers'
]);

myApp.config(['$routeProvider', function($routeProvider) {
    $routeProvider.
    when('/usersTable', {
        templateUrl: '../static/partials/usersTable.html',
        controller: 'UserListController'
    }).
    when('/usersView/:userId', {
        templateUrl: '../static/partials/usersView.html',
        controller: 'UserViewController'
    }).
    when('/usersForm', {
        templateUrl: '../static/partials/usersForm.html',
        controller: 'UserFormController'
    }).
    otherwise({
        redirectTo: '/usersTable'
    });
}]);



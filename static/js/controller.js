'use strict';

    var userControllers = angular.module("userControllers", []);

    userControllers.controller("UserListController", ['$scope', '$http', function($scope, $http) {
      $http.get('/api/user/').
        success(function(data, status, headers, config) {
          $scope.users = data.data;
        }).
        error(function(data, status, headers, config) {
          // log error
        });
    }]);


    userControllers.controller("UserViewController", ['$scope', '$http', '$routeParams', function($scope, $http, $routeParams) {
      $http.get('/api/user/'+$routeParams.userId).
        success(function(data, status, headers, config) {
          $scope.users = data.data;
        }).
        error(function(data, status, headers, config) {
          // log error
        });
    }]);


    userControllers.controller("UserFormController",['$scope', '$http', '$routeParams', '$location', function($scope, $http, transformRequestAsFormPost, $location ) {
        $scope.submit = function() {
            $scope.user.username = $scope.user.email;
            var data = $scope.user;
            console.log(data);
            $http({
              url: "/api/user/",
              method: "POST",
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              data: $.param({"data":JSON.stringify(data)})
            }).success(function(data) {
              console.log(data)
              $location.path( "/usersTable");
            });
        };
    }]);


    userControllers.controller("UserEditFormController",['$scope', '$http', '$routeParams', '$location', function($scope, $http, $routeParams, $location, transformRequestAsFormPost) {

        $http.get('/api/user/'+$routeParams.userId).
            success(function(data, status, headers, config) {
              $scope.user = data.data[0];
            }).
            error(function(data, status, headers, config) {
              // log error
        });


        $scope.submit = function() {
            $scope.user.username = $scope.user.email;
            var data= $scope.user;
            console.log(data);
            $http({
              url: '/api/user/'+$routeParams.userId,
              method: 'PUT',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              data: $.param({"data":JSON.stringify(data)})
            }).success(function(data) {
              console.log(data)
              $location.path( "/usersTable");
            });
        };
    }]);



     userControllers.controller("UserDeleteController",['$scope', '$http', '$routeParams', '$location', function($scope, $http, $routeParams, $location,transformRequestAsFormPost) {
            $http({
              url: '/api/user/'+$routeParams.userId,
              method: "DELETE",
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              data: "{null}"
            }).success(function(data) {
              console.log(data)
              $location.path( "/usersTable");
            });


          $http.get('/api/user/').
            success(function(data, status, headers, config) {
              $scope.users = data.data;
            }).
            error(function(data, status, headers, config) {
              // log error
            });
    }]);



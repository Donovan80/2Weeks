'use strict';

var billsAppControllers = angular.module("billsAppControllers", []);
var loginAppControllers = angular.module("loginAppControllers", []);
var menuBarAppControllers = angular.module("menuBarAppControllers", []);



/***********************
* BILL PREP CONTROLLER *
************************/
billsAppControllers.controller("billFormController",['$scope', '$http', '$routeParams', '$location', 'Bill', 'notificationService', '$modal', function($scope, $http, transformRequestAsFormPost, $location, Bill, notificationService, $modal) {
    $scope.date = new Date();
    $scope.animationsEnabled = true

    $scope.editBill = function (index) {
        console.log(index);
        console.log($scope.bills.indexOf(index));
        var modalInstance = $modal.open({
          animation: $scope.animationsEnabled,
          templateUrl: '/static/partials/form_bill.html',
          controller: 'BillFormModalController',
          resolve: {
            data: function () {
              return angular.copy($scope.bills[$scope.bills.indexOf(index)]);
            }
          }
        });

        modalInstance.result.then(function (newBill) {
          $scope.bills.splice($scope.bills.indexOf(index), 1);
          $scope.bills.push(newBill);
        }, function () {
          console.log('Modal dismissed at: ' + new Date());
        });
      };


    $scope.newBill = function () {
        var modalInstance = $modal.open({
          animation: $scope.animationsEnabled,
          templateUrl: '/static/partials/form_bill.html',
          controller: 'BillFormModalController',
          resolve: {
            data: function () {
              return null;
            }
          }
        });

        modalInstance.result.then(function (newBill) {
          $scope.bills.push(newBill);
        }, function () {
          console.log('Modal dismissed at: ' + new Date());
        });
      };


    //Convert dates in the bills array
    var log = [];
    Bill.query(function(data) {
        $scope.bills = data.data;
        angular.forEach($scope.bills,function(value,index){
            $scope.bills[index].due_date = new Date($scope.bills[index].due_date);
            $scope.bills[index].total_due = parseFloat($scope.bills[index].total_due);
        });
     });

    $scope.submit = function() {
       var data = $scope.bill;
       console.log(data);
       Bill.save(JSON.stringify(data), function(data) {
            console.log(data);
            $scope.bills.push(data.data);
            notificationService.success("Bill Created")
       });
    };

    $scope.deleteBill = function(index, $window, $location) {
       console.log('attempting to delete bill index #'+index);
       var data = $scope.bills[$scope.bills.indexOf(index)];
       Bill.delete({billId: data.id}, function(data) {
        $scope.bills.splice($scope.bills.indexOf(index), 1);
        notificationService.notice("Bill Deleted")
       });
    };

    $scope.differenceInDays = function(first_date) {
        var today = new Date();
        var millisecondsPerDay = 1000 * 60 * 60 * 24;
        var millisBetween = first_date.getTime() - today.getTime();
        var days = millisBetween / millisecondsPerDay
        return Math.floor(days);
    };


}]);







/*****************************
* BILL FORM MODAL CONTROLLER *
******************************/
billsAppControllers.controller('BillFormModalController', ['$scope', '$modalInstance', 'Bill', 'notificationService', 'data', function ($scope, $modalInstance, Bill, notificationService, data) {
    var action = 'new';


    if(data != null){
        var action = 'edit';
        $scope.model = data;
        $scope.model.due_date = new Date(data.due_date);
    }

    $scope.formFields = [
                            {
                                key: 'name',
                                type: 'input',
                                templateOptions: {
                                    type: 'text',
                                    label: 'name',
                                    placeholder: 'Name of Bill',
                                    required: true
                                }
                            },
                            {
                                key: 'total_due',
                                type: 'input',
                                templateOptions: {
                                    addonLeft: {
                                        text:'$'
                                    },
                                    type: 'number',
                                    label: 'Total Due',
                                    required: true
                                }
                            },
                            {
                                key: 'due_date',
                                type: 'input',
                                templateOptions: {
                                    type: 'date',
                                    label: 'Due Date',
                                    required: true
                                }
                            }
                        ];


    var backup = data;
    console.log($scope.model);

    $scope.submitModalForm = function(data) {
        //need to convert strings to date for persistance through application;
        $scope.model.due_date = new Date($scope.model.due_date);
        var data = $scope.model;
        if(action == "edit"){
           console.log(data);
           Bill.put({billId: data.id}, JSON.stringify(data), function(data) {
                if(data.error == null){
                    data.data.due_date = new Date(data.data.due_date);
                    data.data.total_due = parseFloat(data.data.total_due);
                    $modalInstance.close(data.data);
                    notificationService.success("Bill Updated");
                }else{
                    notificationService.error("Error: "+data.error);
                }
           }, function(error){
                console.log(error);
                notificationService.error("Received error status '"+error.status+"': "+error.statusText);
                $scope.bill = backup;
               });
        }else{
           console.log(data);
           Bill.save(JSON.stringify(data), function(data) {
                if(data.error == null){
                    console.log(data.data);
                    data.data.due_date = new Date(data.data.due_date);
                    data.data.total_due = parseFloat(data.data.total_due);
                    $modalInstance.close(data.data);
                    notificationService.success("Bill Added");
                }else{
                    notificationService.error("Error: "+data.error);
                }
           }, function(error){
                console.log(error);
                notificationService.error("Received error status '"+error.status+"': "+error.statusText);
                $scope.bill = backup;
               });

        }

    };


  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };


}]);






loginAppControllers.controller("loginAppLoginController",['$scope', '$routeParams', '$location', 'Login', 'notificationService', function($scope, transformRequestAsFormPost, $location, Login, notificationService) {

     $scope.model = {};

     $scope.formFields = [
                            {
                                key: 'username',
                                type: 'input',
                                templateOptions: {
                                    type: 'text',
                                    label: 'username',
                                    placeholder: 'your@email.com',
                                    required: true
                                }
                            },
                            {
                                key: 'password',
                                type: 'input',
                                templateOptions: {
                                    type: 'password',
                                    label: 'password',
                                    required: true
                                }
                            }
                        ];

     $scope.submit = function() {
        if($scope.model.username == null || $scope.model.password == null){
             notificationService.error("Please Enter username and password")
        }else{
            Login.save(JSON.stringify({username: $scope.model.username, password: $scope.model.password}), function(data){
                console.log(data)
                if(data.error == null){
                    window.location.href = '/home/';
                }else{
                    notificationService.error(data.error)
                    console.log(data.error);
                }
            });
        }
    }
}]);





loginAppControllers.controller("loginAppRegisterController",['$scope', '$http', '$routeParams', '$location','$window', function($scope, $http, transformRequestAsFormPost, $location) {
    $scope.submit = function($window, $location) {
        $http({
          url: "/api/login/",
          method: "POST",
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
           data: $.param({username: $scope.username, password: $scope.password})
        }).success(function(data) {
          console.log(data)
          window.location.href = '/home/';
        });
    };
}]);






menuBarAppControllers.controller('menuBarAppController',['$scope', '$http', '$location', function($scope, $http, $location ) {
 //console.log('logging out');
  $scope.logout = function($window, $location) {
    console.log('logging out');
        $http.get('/api/logout/').
            success(function(data, status, headers, config) {
                window.location.href = '/';
            }).
            error(function(data, status, headers, config) {
                console.log('could not logout');
        });
    };
}]);




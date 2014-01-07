from google.appengine.ext import ndb

import webapp2
import json

class IdModel(ndb.Model):
    
    def to_dict(self, include=None, exclude=None):
        d =  ndb.Model.to_dict(self, include=include, exclude=exclude)
        d['id'] = self.key.id()
        return d

class Sport(IdModel):
    name = ndb.StringProperty(required=True)

class Spot(IdModel):
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)
    sports = ndb.KeyProperty(kind=Sport, repeated=True)
    latitude = ndb.FloatProperty(required=True)
    longitude = ndb.FloatProperty(required=True)
    creator = ndb.IntegerProperty(required=True)
    groups = ndb.IntegerProperty(repeated=True)
    
    def to_dict(self, include=None, exclude=None):
        d = IdModel.to_dict(self, include=include, exclude=exclude)
        d['sports'] = [s.get().to_dict() for s in self.sports]
        return d

class Group(IdModel):
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)
    sport = ndb.KeyProperty(kind=Sport, required=True)
    users = ndb.IntegerProperty(repeated=True)
    spots = ndb.IntegerProperty(repeated=True)
    
    def to_dict(self, include=None, exclude=None):
        d = IdModel.to_dict(self, include=include, exclude=exclude)
        d['sport'] = self.sport.get().to_dict()
        return d
    
class User(IdModel):
    name = ndb.StringProperty(required=True)
    facebookId = ndb.StringProperty()
    googleplusId = ndb.StringProperty()
    location = ndb.StringProperty(required=True)
    groups = ndb.IntegerProperty(repeated=True)
    

class ApiSpots(webapp2.RequestHandler):

    def get(self):
        try:
            fromGroup = int(self.request.get('fromGroup',-1)) 
            if fromGroup > 0:
                group = Group.get_by_id(fromGroup)
                response = []
                for i in group.spots:
                    response.append(Spot.get_by_id(i).to_dict())
                self.response.write(json.dumps(response))
                return
            limit = int(self.request.get('limit',999))
            offset = int(self.request.get('offset', 0))
            self.response.write(json.dumps([s.to_dict() for s in Spot.query().order(Spot.name).fetch(limit=limit, offset=offset)]))
        except Exception as e:
            self.response.write(error(str(e)))


class ApiEditSpot(webapp2.RequestHandler):

    def post(self):
        try:
            pid = self.request.get('id')
            pname = self.request.get('name')
            pdescription = self.request.get('description')
            psports = self.request.get('sports')
            platitude = float(self.request.get('latitude'))
            plongitude = float(self.request.get('longitude'))
            pcreator = int(self.request.get('creator', -1))
            
            if len(pid) > 0: 
                spot = Spot.get_by_id(int(pid))
            else:
                spot = Spot()
            
            if spot is None:
                self.response.write(error('There is no Spot with this id.'))
                return
            
            if pname: spot.name = pname
            if pdescription: spot.description = pdescription
            if psports: 
                for psport in psports.split(','):
                    sport = Sport.get_by_id(int(psport))
                    if sport is None:
                        self.response.write(error('There is no Sport with this id = %s.' % psport))
                        return
                    spot.sports.append(sport.key)
            if platitude: spot.latitude = platitude
            if plongitude: spot.longitude = plongitude
            if pcreator > 0: 
                spot.creator = pcreator
            else:
                self.response.write(error('You have to assign a creator.'))
                return
            
            if len(spot.sports) == 0:
                self.response.write(error('You have to assign at least one sport.'))
                return
    
            spot.put()
            
            self.response.write(json.dumps(spot.to_dict()))
        except Exception as e:
            self.response.write(error(str(e)))
            
class ApiSports(webapp2.RequestHandler):

    def get(self):
        self.response.write(json.dumps([s.to_dict() for s in Sport.query().fetch()]))


class ApiEditSport(webapp2.RequestHandler):

    def post(self):
        try:
            pid = self.request.get('id')
            pname = self.request.get('name')
            
            if len(pid) > 0: 
                sport = Sport.get_by_id(int(pid))
            else:
                sport = Sport()
            
            if sport is None:
                self.response.write(error('There is no Sport with this id.'))
                return
            
            if pname: sport.name = pname
    
            sport.put()
            
            self.response.write(json.dumps(sport.to_dict()))
        except Exception as e:
            self.response.write(error(str(e)))
            
class ApiGroups(webapp2.RequestHandler):

    def get(self):
        try:
            fromSpot = int(self.request.get('fromSpot',-1))
            fromUser = int(self.request.get('fromUser',-1))
            if fromSpot > 0 and fromUser > 0:
                self.response.write(error('You should use only one of "fromSpot" or "fromUser".'))
                return
            idlist = None
            if fromSpot > 0:
                idlist = Spot.get_by_id(fromSpot).groups
            elif fromUser > 0:
                idlist = User.get_by_id(fromUser).groups
            
            if idlist is not None:
                self.response.write(json.dumps([Group.get_by_id(g).to_dict() for g in idlist]))
                return
            
            self.response.write(json.dumps([g.to_dict() for g in Group.query().order(Group.name)]))
        except Exception as e:
            self.response.write(error(str(e)))


class ApiEditGroup(webapp2.RequestHandler):

    def post(self):
        try:
            pid = self.request.get('id')
            pname = self.request.get('name')
            pdescription = self.request.get('description')
            psport = self.request.get('sport')
            pcreator = int(self.request.get('creator',0))
            
            if len(pid) > 0: 
                group = Group.get_by_id(int(pid))
            else:
                if(pcreator <= 0):
                    self.response.write(error('You have to set "creator" when creating a new Group.'))
                    return
                group = Group()
                group.users.append(pcreator)
                creator = User.get_by_id(pcreator)
                
                
            if group is None:
                self.response.write(error('There is no Group with this id.'))
                return
            
            if pname: group.name = pname
            if pdescription: group.description = pdescription
            if psport: 
                sport = Sport.get_by_id(int(psport))
                if sport is None:
                    self.response.write(error('There is no Sport with this id = %s.' % psport))
                    return
                group.sport = sport.key
            
            group.put()
            
            if creator is not None:
                creator.groups.append(group.key.id())
                creator.put()
            
            self.response.write(json.dumps(group.to_dict()))
        except Exception as e:
            self.response.write(error(str(e)))   
            
class ApiUsers(webapp2.RequestHandler):

    def get(self):
        try:
            pid = int(self.request.get('id',-1))
            fromGroup = int(self.request.get('fromGroup',-1))
            if pid > 0 and fromGroup > 0:
                self.response.write(error('You should use only one of "id" or "fromGroup".'))
                return
            if pid > 0:
                self.response.write(json.dumps(User.get_by_id(pid).to_dict()))
                return
            if fromGroup > 0:
                self.response.write(json.dumps([User.get_by_id(u).to_dict() for u in Group.get_by_id(fromGroup).users]))
                return
            
            self.response.write(json.dumps([u.to_dict() for u in User.query().order(User.name)]))
        except Exception as e:
            self.response.write(error(str(e)))


class ApiEditUser(webapp2.RequestHandler):

    def post(self):
        try:
            pid = self.request.get('id')
            pname = self.request.get('name')
            plocation = self.request.get('location')
            pfacebookId = self.request.get('facebookId')
            pgoogleplusId = self.request.get('googleplusId')
            
            if len(pid) > 0: 
                user = User.get_by_id(int(pid))
                if user is None:
                    self.response.write(error('There is no User with this id.'))
                    return
            elif len(pfacebookId) > 0: 
                users = User.query(ndb.GenericProperty('facebookId') == pfacebookId).fetch()
		if len(users) > 0:
			user = users[0]
		else:
			user = User()
            elif len(pgoogleplusId) > 0: 
                users = User.query(ndb.GenericProperty('googleplusId') == pgoogleplusId).fetch()
		if len(users) > 0:
			user = users[0]
		else:
			user = User()

            
            if pname: user.name = pname
            if plocation: user.location = plocation
            if pfacebookId: user.facebookId = pfacebookId
            if pgoogleplusId: user.googleplusId = pgoogleplusId
            
            user.put()
            
            self.response.write(json.dumps(user.to_dict()))
        except Exception as e:
            self.response.write(error(str(e)))   
            
class ApiInOutGroup(webapp2.RequestHandler):

    def post(self):
        try:
            puserid = self.request.get('userId')
            pgroupid = self.request.get('groupId')
            pinOrOut = self.request.get('inOrOut')
            
            if len(puserid) > 0: 
                user = User.get_by_id(int(puserid))
            
            if user is None:
                self.response.write(error('There is no User with this id.'))
                return
            
            if len(pgroupid) > 0: 
                group = Group.get_by_id(int(pgroupid))
            
            if group is None:
                self.response.write(error('There is no Group with this id.'))
                return
            
            if pinOrOut == 'in' :
                if group.key.id() not in user.groups:
                    user.groups.append(group.key.id())
                    user.put()
                if user.key.id() not in group.users:
                    group.users.append(user.key.id())
                    group.put()
            else:
                if group.key.id() in user.groups:
                    user.groups.remove(group.key.id())
                    user.put()
                if user.key.id() in group.users:
                    group.users.remove(user.key.id())
                    group.put()
            self.response.write(RESULT_OK)
        except Exception as e:
            self.response.write(error(str(e)))      
            
class ApiLinkGroupSpot(webapp2.RequestHandler):

    def post(self):
        try:
            pspotid = self.request.get('spotId')
            pgroupid = self.request.get('groupId')
            plinkOrUnlink = self.request.get('linkOrUnlink')
            
            if len(pspotid) > 0: 
                spot = Spot.get_by_id(int(pspotid))
            
            if spot is None:
                self.response.write(error('There is no Spot with this id.'))
                return
            
            if len(pgroupid) > 0: 
                group = Group.get_by_id(int(pgroupid))
            
            if group is None:
                self.response.write(error('There is no Group with this id.'))
                return
            
            if plinkOrUnlink == 'link' :
                if group.key.id() not in spot.groups:
                    spot.groups.append(group.key.id())
                    spot.put()
                if spot.key.id() not in group.spots:
                    group.spots.append(spot.key.id())
                    group.put()
            else:
                if group.key.id() in spot.groups:
                    spot.groups.remove(group.key.id())
                    spot.put()
                if spot.key.id() in group.spots:
                    group.spots.remove(spot.key.id())
                    group.put()
            self.response.write(RESULT_OK)
        except Exception as e:
            self.response.write(error(str(e)))            


application = webapp2.WSGIApplication([
    ('/api/spots', ApiSpots),
    ('/api/edit_spot', ApiEditSpot),
    ('/api/sports', ApiSports),
    ('/api/edit_sport', ApiEditSport),
    ('/api/groups', ApiGroups),
    ('/api/edit_group', ApiEditGroup),
    ('/api/users', ApiUsers),
    ('/api/edit_user', ApiEditUser),
    ('/api/inout_group', ApiInOutGroup),
    ('/api/linkgroupspot', ApiLinkGroupSpot),
], debug=True)
                                
def error(msg):
    return '{"error":"' + msg + '"}'

RESULT_OK = '{ "result":"OK" }';

